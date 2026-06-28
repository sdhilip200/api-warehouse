---
name: validate
description: >
  Use this skill when the user wants to validate loaded data, reconcile API vs
  warehouse counts, run control-total checks, verify completeness of a landing run,
  or compare source records against what was loaded.
  Trigger phrases include: "validate loaded data", "reconcile counts", "control totals",
  "check completeness", "verify the load", "compare API vs warehouse", or any request
  to confirm that loaded rows match the source API.
---

# validate — Best-Effort Control-Total Reconciliation

## Overview

This skill re-pulls a bounded sample from the source API, profiles both the source
sample and the loaded warehouse table, reconciles the two profiles, and renders a
`validation.html` report.

**Validation is best-effort.** When the API does not expose a total-row-count endpoint,
or when column types differ between source and destination, individual checks are marked
`skipped` rather than fabricated. Never claim an exact match that was not actually
computed.

**Pre-requisites:**
- `endpoints.json` produced by `assess` must exist.
- The warehouse table loaded by `land` must be queryable.

---

## Step 1 — Confirm What to Validate

Ask the user:

> Which endpoint / table should we validate?
> Please provide:
> 1. The endpoint name (from `endpoints.json`) to re-pull from the source API.
> 2. The warehouse table name (e.g. `raw.posts`) to compare against.
> 3. A row limit for the source re-pull (default: 1000 rows — keep it bounded).

Wait for the user's answer before continuing.

---

## Step 2 — Re-pull a Bounded Source Sample

Read `endpoints.json` to get the endpoint URL, auth config, and pagination settings.
Fetch up to the agreed row limit from the source API. Use the same auth approach
as `land` (bearer token from env var if `auth.type == "bearer"`):

```python
import json, os, requests

with open("endpoints.json") as f:
    spec = json.load(f)

# Locate the target endpoint
endpoint = next(ep for ep in spec["endpoints"] if ep["name"] == TARGET_ENDPOINT)
url = spec["base_url"].rstrip("/") + endpoint["path"]
headers = {}
if spec["auth"]["type"] == "bearer":
    token_env = spec["auth"]["token_env"]
    headers["Authorization"] = f"Bearer {os.environ[token_env]}"

# Fetch bounded pages until ROW_LIMIT is reached
source_records = []
params = {"per_page": 100}  # adjust to API's page-size parameter name
while url and len(source_records) < ROW_LIMIT:
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    page = resp.json()
    # Unwrap list at known key, or use list directly
    rows = page if isinstance(page, list) else page.get(endpoint["name"], page.get("data", page.get("results", [])))
    source_records.extend(rows)
    # Follow next-page link if present; stop when none
    url = (page.get("links") or {}).get("next") or (page.get("pagination") or {}).get("next_url")
    params = {}  # next-page URL already contains params

source_records = source_records[:ROW_LIMIT]
print(f"Source sample: {len(source_records)} records")
```

If the API returns no usable total-count header or next-page link, note this — the
row-count check may be `skipped`.

---

## Step 3 — Query the Warehouse Table

Pull the same rows from the loaded table. Use the destination's native client:

```python
# DuckDB example
import duckdb
con = duckdb.connect("warehouse.duckdb")
loaded_records = con.execute(f"SELECT * FROM {WAREHOUSE_TABLE} LIMIT {ROW_LIMIT}").df().to_dict(orient="records")
print(f"Loaded sample: {len(loaded_records)} records")
```

Adapt to BigQuery / Snowflake / Postgres as needed (see `references/destinations.md`).

---

## Step 4 — Profile Both Sides

```python
from api_warehouse.profile import profile_records

source_profile = profile_records(source_records)
loaded_profile = profile_records(loaded_records)

print("Source profile:", source_profile["row_count"], "rows,", len(source_profile["columns"]), "columns")
print("Loaded profile:", loaded_profile["row_count"], "rows,", len(loaded_profile["columns"]), "columns")
```

`profile_records` returns `{"row_count": int, "columns": {name: {type, null_count, ...}}}`.

---

## Step 5 — Reconcile

```python
from api_warehouse.reconcile import reconcile

result = reconcile(source_profile, loaded_profile)
# result: {"checks": [...], "ok": bool}
# Each check: {"name": str, "kind": str, "status": "pass"|"fail"|"skipped", "detail": str}

passed  = sum(1 for c in result["checks"] if c["status"] == "pass")
failed  = sum(1 for c in result["checks"] if c["status"] == "fail")
skipped = sum(1 for c in result["checks"] if c["status"] == "skipped")
print(f"Reconciliation: {passed} passed, {failed} failed, {skipped} skipped")
```

Checks are marked `skipped` (not `fail`) when:
- A count or stat is unavailable on one or both sides.
- Column types differ between source and warehouse.
- No comparable statistic exists for a column type.

Do **not** treat `skipped` as a failure; report it honestly as "check not computable."

---

## Step 6 — Render the Validation Report

```python
from api_warehouse.report import render_validation

html = render_validation(result)
with open("validation.html", "w") as f:
    f.write(html)
print("Report written to validation.html")
```

`render_validation` accepts the dict returned by `reconcile` and produces a
self-contained `validation.html` with pass/fail/skipped rows colour-coded.

---

## Step 7 — Present Results

Tell the user the reconciliation summary:

> Validation complete.
> - **X** checks passed
> - **Y** checks failed
> - **Z** checks skipped (source stat unavailable or types differ)
>
> Report saved to `validation.html`. Open it in a browser to inspect each check.

If any checks **failed**:
- Row-count mismatch → the load may be incomplete. Re-run `land` or investigate
  pagination gaps.
- Numeric sum mismatch → possible data transformation or rounding issue.
- Timestamp range mismatch → possible timezone normalisation difference.

If checks are **skipped**:
- Remind the user that skipped checks mean the comparison was not possible, not
  that data is correct or incorrect. Consider widening the sample or using a
  full-table count query if the source API supports it.

Do **not** claim completeness when some checks are skipped.
