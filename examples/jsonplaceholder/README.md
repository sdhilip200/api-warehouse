# Worked Example: JSONPlaceholder → DuckDB

This walkthrough shows the full api-warehouse loop against [JSONPlaceholder](https://jsonplaceholder.typicode.com) — a free, public REST API that requires no API key. It mirrors the automated end-to-end test in [`tests/test_e2e_jsonplaceholder.py`](../../tests/test_e2e_jsonplaceholder.py).

---

## Prerequisites

```bash
pip install -e ".[dev]"
```

No credentials required — JSONPlaceholder is public.

---

## Step 1: Assess

```
/assess https://jsonplaceholder.typicode.com
```

The `assess` skill fetches the API docs, probes the available endpoints, and produces:

**`assessment.html`** — a client-ready report containing:
- Endpoint inventory (`/posts`, `/comments`, `/albums`, `/photos`, `/todos`, `/users`)
- Auth: none required
- Pagination: none (small dataset, full response)
- Incremental support verdict: **not supported** (no cursor/watermark fields in responses — evidence: no `updated_at` or equivalent field in `/posts` response)
- Volume estimate: 100 posts, 500 comments, 200 albums, 5000 photos, 200 todos, 10 users
- Rate limits: none documented

**`endpoints.json`** — machine-readable endpoint spec for the `land` skill:
```json
{
  "base_url": "https://jsonplaceholder.typicode.com",
  "auth": {"type": "none"},
  "paginator": {"type": "single_page"},
  "resources": [
    {
      "name": "posts",
      "path": "/posts",
      "primary_key": "id",
      "incremental": null
    }
  ]
}
```

**`samples/posts.json`** — first 3 rows of `/posts` for client sign-off:
```json
[
  {"userId": 1, "id": 1, "title": "sunt aut facere ...", "body": "quia et suscipit ..."},
  {"userId": 1, "id": 2, "title": "qui est esse", "body": "est rerum tempore ..."},
  {"userId": 1, "id": 3, "title": "ea molestias quasi ...", "body": "et iusto sed ..."}
]
```

---

## Step 2: Checkpoint

The `assess` skill pauses and presents the report. Confirm:
- Which endpoints to land (e.g., just `posts`)
- Destination (`duckdb` for local dev, `postgres` for staging)
- Load mode (`replace` for full refresh, since no incremental cursor)

---

## Step 3: Land

```
/land posts --destination duckdb
```

The `land` skill:
1. Reads `endpoints.json`
2. Calls `build_rest_api_config(spec, secrets={})` to build the dlt pipeline config
3. Runs `dlt pipeline run` loading `/posts` into DuckDB at `warehouse.duckdb`

Expected output:
```
Loaded 100 rows into posts (DuckDB: warehouse.duckdb)
```

To land into Postgres instead, set credentials in `.dlt/secrets.toml`:

```toml
[destination.postgres]
connection_string = "postgresql://user:pass@host:5432/db"  # replace with your own connection string (never commit real credentials)
```

Then run:
```
/land posts --destination postgres
```

---

## Step 4: Validate

```
/validate
```

The `validate` skill:
1. Fetches the source count from `/posts` (100 rows)
2. Queries the destination table: `SELECT COUNT(*) FROM posts` (100 rows)
3. Computes the control total: source 100 == loaded 100 → **PASS**

**`validation.html`** — the validation report:

```
API Assessment Validation Report
=================================
Endpoint: /posts
  Source count (API):   100
  Loaded count (dest):  100
  Delta:                0
  Status:               PASS

Notes:
  - Incremental cursor: N/A (full refresh)
  - Duplicate check: skipped (no primary key dedup configured)
```

---

## Running the automated test

The same scenario is covered by the e2e test:

```bash
pytest tests/test_e2e_jsonplaceholder.py -v
```

This runs without any credentials and validates that:
- `profile_records` returns at least 1 endpoint for JSONPlaceholder
- `reconcile` returns a delta of 0 for the posts endpoint
- The HTML report contains the word "PASS"
