---
name: assess
description: >
  Use this skill when the user wants to assess an API, read API documentation,
  build an API assessment, or prepare a data pipeline spec from API docs.
  Trigger phrases include: "assess this API", "read these API docs", "build an
  API assessment", "can we pull data from this API", "analyze this API", or any
  request to evaluate an API before building a pipeline.
---

# assess — API Documentation Analysis and Assessment

## Overview

This skill reads API documentation and produces three artifacts:
- `samples/` — real rows fetched from key endpoints
- `endpoints.json` — the machine-readable spec consumed by `pipeline.build_rest_api_config`
- `assessment.html` — a client-ready HTML report rendered via `api_warehouse.report.render_assessment`

Later skills (`land`, `validate`) assume this step is complete and `endpoints.json` exists.

---

## Step 0 — Input Guard

Before any analysis, confirm the input is genuine API documentation. Look for:
- At least one concrete HTTP endpoint (a URL path like `/v1/users`)
- HTTP methods (`GET`, `POST`, etc.)
- Auth instructions (API key, Bearer token, OAuth, or explicitly "no auth")

If those signals are absent, **STOP** and say exactly:

> This doesn't look like API documentation — I can't find endpoints, methods, or auth. Did you mean a different link?

*(The phrase "not API documentation" is the key signal that the input guard has fired.)*

Do not attempt any further steps until the user provides valid API docs.

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

Assess three capability areas, referencing the project's canonical references:

### Pagination
Identify the pagination style and record the mechanism. See `references/pagination-patterns.md` for the full pattern catalogue. Common types:

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
- `"supported": true` requires a named filter parameter **OR** a named cursor/updated-at response field as evidence — either is sufficient (requiring both wrongly excludes valid change-feed endpoints).
- Never set `"supported": true` without concrete evidence from the docs.
- Never guess — if the evidence is ambiguous, set `false` and explain.

---

## Step 4 — Intent Interview

Ask the user two questions before writing any artifacts:

1. **Volume** — roughly how many records exist and how often they change? (helps choose batch size and schedule)
2. **Load strategy** — do you want a one-time raw snapshot, or ongoing incremental updates?

Reconcile their answer against the incremental verdict:
- If they want incremental but `"supported": false` — explain the limitation; offer full-replace on a schedule as an alternative.
- If they want one-time raw but `"supported": true` — note that incremental is available if they change their mind later.

---

## Step 5 — Sample Pull

For each key endpoint (start with the primary resource endpoint), fetch a small real sample and save it:

```bash
# Example: fetch first page of users
curl -s -H "Authorization: Bearer $MY_API_TOKEN" \
  "https://api.example.com/v1/users?per_page=5" \
  | python3 -m json.tool > samples/users.json
```

- Save each sample as `samples/<endpoint_name>.json`
- Scrub any PII or sensitive values before saving (see `references/security.md`)
- Note the actual field names and types from the live response — they may differ from the docs

---

## Step 6 — Write Artifacts

### 6a. Assemble `endpoints.json`

Write `endpoints.json` in the project root. This is the exact shape consumed by `api_warehouse/pipeline.py` `build_rest_api_config`:

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
- `base_url` — full base URL without trailing slash
- `auth.type` — `none` | `bearer` | `api_key`
- `auth.token_env` — env-var name holding the secret (for `bearer` and `api_key`)
- `auth.name` / `auth.location` — header/param name and `header`|`query` location (for `api_key` only)
- `paginator` — omit or set `type: single_page` if there is no pagination
- `resources[].incremental` — set to `null` if not supported; otherwise provide `cursor_path`, `param`, and `initial_value`

### 6b. Render `assessment.html`

Assemble the assessment dict and render the HTML report:

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
# Note: render_assessment shows incremental detail from the `evidence` key (supported) or the `reason` key (not supported); include one of them in the incremental dict.
```

---

## Step 7 — Checkpoint

Tell the user:

> `assessment.html` is ready. Please open it, review the endpoint list and incremental verdict, and confirm the scope before we proceed to `land`. Share it with your client for sign-off if needed.

Do **not** run `land` until the user explicitly confirms scope.
