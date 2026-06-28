---
name: assess
description: >
  Use this skill whenever the user points at API docs, a docs URL, or an OpenAPI
  spec and wants to understand endpoints, auth, pagination, incremental support,
  or wants an API assessment, sample data, or to scope an ingestion — even if
  they don't say "assess". Trigger phrases include: "assess this API", "read
  these API docs", "can we pull data from this API", "what endpoints does this
  have", "analyze this API", "is this API incremental", "build a pipeline from
  this spec", or any request to evaluate or explore an API before building a
  pipeline.
---

# assess — API Documentation Analysis and Assessment

This skill reads API documentation and produces three artifacts:
- `samples/` — real rows fetched from key endpoints
- `endpoints.json` — the machine-readable spec consumed by `api_warehouse/pipeline.py build_rest_api_config`
- `assessment.html` — a client-ready HTML report rendered via `api_warehouse/report.py render_assessment`

Later skills (`land`, `validate`) assume this step is complete and `endpoints.json` exists.

---

## Step 0 — Input Guard

Before any analysis, confirm the input is genuine API documentation. Look for:
- At least one concrete HTTP endpoint (a URL path like `/v1/users`)
- HTTP methods (`GET`, `POST`, etc.)
- Auth instructions (API key, Bearer token, OAuth, or explicitly "no auth")

If those signals are absent, stop and say exactly:

> This doesn't look like API documentation — I can't find endpoints, methods, or auth. Did you mean a different link?

The phrase "not API documentation" in that reply is the signal that the input guard has fired. Do not attempt any further steps until the user provides valid API docs.

---

## Step 1 — Endpoint Inventory

List every endpoint found in the docs as a table:

| Name | Method | Path | Key Params | Response Fields |
|------|--------|------|-----------|----------------|
| list_users | GET | /v1/users | page, per_page, updated_after | id, name, email, updated_at |

For each endpoint, record:
- **Name** — a snake_case identifier (e.g. `list_orders`)
- **Method** — HTTP verb
- **Path** — relative to the base URL
- **Key params** — pagination, filtering, and cursor/timestamp params
- **Response fields** — top-level fields and their types; note any nested arrays that are the actual data

---

## Step 2 — Capabilities

### Pagination

Identify the pagination style. See `references/pagination-patterns.md` for the full catalogue. Common types:

| Type | Signals |
|------|---------|
| `page_number` | `page` + `per_page` params; `total_pages` in response |
| `cursor` | `cursor` or `next_cursor` field returned with each page |
| `link_header` | `Link: <url>; rel="next"` response header |
| `offset` | `offset` + `limit` params |
| `single_page` | No pagination — all records in one response |

### Rate Limits

Record: requests/minute or requests/day limit, retry-after mechanism, and any headers (`X-RateLimit-Remaining`, `Retry-After`).

### Auth

Identify the auth type and the exact header or parameter name. See `references/auth-patterns.md`. Record as the `auth` block you will write into `endpoints.json`:
- `none` — public API
- `bearer` — `Authorization: Bearer <token>`
- `api_key` — custom header or query param

---

## Step 3 — Incremental Verdict

Follow the decision rules in `references/incremental-detection.md` exactly. Produce a JSON verdict:

```json
{"supported": true, "evidence": "updated_at field on all records; updated_after query param documented"}
```

or

```json
{"supported": false, "reason": "No timestamp fields or cursor params in any endpoint"}
```

Rules:
- `"supported": true` requires a named filter parameter or a named cursor/updated-at response field as evidence — either is sufficient (requiring both wrongly excludes valid change-feed endpoints).
- Never set `"supported": true` without concrete evidence from the docs.
- If evidence is ambiguous, set `false` and explain rather than guessing.

---

## Step 4 — Intent Interview

Ask the user two questions before writing any artifacts:

1. **Volume** — roughly how many records exist and how often they change? (This determines batch size and schedule.)
2. **Load strategy** — one-time raw snapshot, or ongoing incremental updates?

Reconcile the answer against the incremental verdict:
- If they want incremental but `"supported": false`: explain the limitation; offer full-replace on a schedule as an alternative.
- If they want a one-time raw snapshot but `"supported": true`: note that incremental is available if they change their mind.

---

## Step 5 — Sample Pull

For each key endpoint (start with the primary resource), fetch a small real sample and save it:

```bash
curl -s -H "Authorization: Bearer $MY_API_TOKEN" \
  "https://api.example.com/v1/users?per_page=5" \
  | python3 -m json.tool > samples/users.json
```

- Save each sample as `samples/<endpoint_name>.json`
- Scrub any PII or sensitive values before saving (see `references/security.md`)
- Note actual field names and types from the live response — they sometimes differ from the docs

---

## Step 6 — Write Artifacts

Before writing, read `../../references/anti-slop.md` and apply it to any prose you generate in the assessment.

### 6a. Assemble `endpoints.json`

Write `endpoints.json` in the project root. This is the exact shape consumed by `api_warehouse/pipeline.py build_rest_api_config`:

```json
{
  "base_url": "https://api.example.com/v1",
  "auth": {
    "type": "bearer",
    "token_env": "MY_API_TOKEN"
  },
  "paginator": {
    "type": "page_number",
    "page_param": "page",
    "page_size_param": "per_page",
    "page_size": 100,
    "total_path": "meta.total_pages"
  },
  "resources": [
    {
      "name": "users",
      "path": "/users",
      "primary_key": "id",
      "incremental": {
        "cursor_path": "updated_at",
        "param": "updated_after",
        "initial_value": "2020-01-01T00:00:00Z"
      }
    },
    {
      "name": "orders",
      "path": "/orders",
      "primary_key": "id",
      "incremental": null
    }
  ]
}
```

Field reference:
- `base_url` — full base URL, no trailing slash
- `auth.type` — `none` | `bearer` | `api_key`
- `auth.token_env` — env-var name holding the secret (for `bearer` and `api_key`)
- `auth.name` / `auth.location` — header/param name and `header`|`query` location (for `api_key` only)
- `paginator` — omit or set `type: single_page` if there is no pagination
- `resources[].incremental` — `null` if not supported; otherwise provide `cursor_path`, `param`, and `initial_value`

### 6b. Render `assessment.html`

```python
from api_warehouse.report import render_assessment

assessment = {
    "api_name": "Example API",
    "base_url": "https://api.example.com/v1",
    "incremental": {
        "supported": True,
        "evidence": "updated_at field + updated_after param"
    },
    "endpoints": [
        {"name": "users",  "method": "GET", "path": "/users",  "primary_key": "id"},
        {"name": "orders", "method": "GET", "path": "/orders", "primary_key": "id"},
    ]
}

html = render_assessment(assessment)
with open("assessment.html", "w") as f:
    f.write(html)
```

`render_assessment` reads `inc.get("evidence")` when `supported` is true and `inc.get("reason")` when false. Include whichever applies so the HTML shows the verdict with detail.

### 6c. Self-check (eval loop)

After writing both artifacts, run the eval loop defined in `../../references/running-evals.md` using the checklist in `EVALS.md`. Spin up a separate grader agent with a clean context; give it only `EVALS.md`, `endpoints.json`, `assessment.html`, and any `samples/` files. Fix any `fail` verdicts and re-run until all checks are `pass` or `skipped`, up to 5 rounds.

### 6d. Update `MEMORY.md`

Read `MEMORY.md` in this directory. If this API introduced a pagination style, cursor name, auth pattern, or gotcha not already recorded, append a one-line entry. Keep entries terse.

---

## Step 7 — Checkpoint

Tell the user:

> `assessment.html` is ready. Please open it, review the endpoint list and incremental verdict, and confirm scope before we proceed to `land`. Share it with your client for sign-off if needed.

Do not run `land` until the user explicitly confirms scope.
