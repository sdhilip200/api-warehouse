---
name: validate
description: >
  Use whenever the user wants to validate or reconcile loaded data against the source API,
  check row counts or control totals, verify a load was complete, or confirm that warehouse
  data matches what the API returned — even if they don't say "validate". Trigger phrases
  include: "did everything land?", "check the counts", "reconcile the table", "verify the
  load", "compare API vs warehouse", "are the rows correct?", or any request to confirm
  that a loaded table matches its source.
---

# validate — Control-Total Reconciliation

## Overview

Re-pull a bounded sample from the source API, profile both the sample and the loaded
warehouse table with `profile_records`, reconcile the two profiles with `reconcile`, and
write a `validation.html` report via `render_validation`.

Validation is best-effort. When the API exposes no total-count endpoint, or when column
types differ between source and destination, individual checks are marked `skipped` rather
than fabricated. Never claim an exact match that was not actually computed — see
`../../references/anti-slop.md` for the honesty standard this report must meet.

Pre-requisites: `endpoints.json` produced by `assess` must exist; the warehouse table
loaded by `land` must be queryable.

Check `MEMORY.md` before starting — it records API-specific quirks discovered in prior
runs (e.g., endpoints that expose no total count, pagination edge cases).

---

## Step 1 — Confirm What to Validate

Ask the user:

> Which endpoint / table should we validate? Please provide:
> 1. The endpoint name (from `endpoints.json`) to re-pull from the source API.
> 2. The warehouse table name (e.g. `raw.posts`) to compare against.
> 3. A row limit for the source re-pull (default: 1000 rows).

Wait for the user's answer before continuing.

---

## Step 2 — Re-pull a Bounded Source Sample

Read `endpoints.json` and locate the target endpoint by iterating over `spec["resources"]`.
Fetch up to the agreed row limit using the same auth as `land`:

```python
import json, os, requests

with open("endpoints.json") as f:
    spec = json.load(f)

endpoint = next(ep for ep in spec["resources"] if ep["name"] == TARGET_ENDPOINT)
url = spec["base_url"].rstrip("/") + endpoint["path"]
headers = {}
if spec["auth"]["type"] == "bearer":
    token_env = spec["auth"]["token_env"]
    headers["Authorization"] = f"Bearer {os.environ[token_env]}"

source_records = []
params = {"per_page": 100}
while url and len(source_records) < ROW_LIMIT:
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    page = resp.json()
    rows = page if isinstance(page, list) else page.get(endpoint["name"], page.get("data", page.get("results", [])))
    source_records.extend(rows)
    url = (page.get("links") or {}).get("next") or (page.get("pagination") or {}).get("next_url")
    params = {}

source_records = source_records[:ROW_LIMIT]
print(f"Source sample: {len(source_records)} records")
```

If the API returns no usable total-count header or next-page link, note this. The
row-count check will be `skipped` — record the quirk in `MEMORY.md` for future runs.

---

## Step 3 — Query the Warehouse Table

Pull the same number of rows from the loaded table:

```python
# DuckDB example (pandas-free — uses fetchall + con.description)
import duckdb
con = duckdb.connect("warehouse.duckdb")
rows = con.execute(f"SELECT * FROM {WAREHOUSE_TABLE} LIMIT {ROW_LIMIT}").fetchall()
cols = [c[0] for c in con.description]
loaded_records = [dict(zip(cols, r)) for r in rows]
print(f"Loaded sample: {len(loaded_records)} records")
```

Adapt to BigQuery / Snowflake / Postgres using the destination's native client.

---

## Step 4 — Profile Both Sides

Note: dlt snake-cases camelCase field names on load (e.g. `userId` → `user_id`). Normalize
source record keys before profiling so columns align and are not spuriously marked `skipped`.

```python
from api_warehouse.profile import profile_records
from api_warehouse.normalize import normalize_record_keys

source_profile = profile_records(normalize_record_keys(source_records))
loaded_profile = profile_records(loaded_records)

print("Source profile:", source_profile["row_count"], "rows,", len(source_profile["columns"]), "columns")
print("Loaded profile:", loaded_profile["row_count"], "rows,", len(loaded_profile["columns"]), "columns")
```

`profile_records` returns `{"row_count": int, "columns": {name: {type, null_count, ...}}}`.
Numeric columns get `sum/min/max`; timestamp columns get `min/max`; text columns get
`distinct_count` and top-5 values.

---

## Step 5 — Reconcile

```python
from api_warehouse.reconcile import reconcile

result = reconcile(source_profile, loaded_profile)

passed  = sum(1 for c in result["checks"] if c["status"] == "pass")
failed  = sum(1 for c in result["checks"] if c["status"] == "fail")
skipped = sum(1 for c in result["checks"] if c["status"] == "skipped")
print(f"Reconciliation: {passed} passed, {failed} failed, {skipped} skipped")
```

Checks are marked `skipped` when a stat is unavailable on either side, column types differ,
or no comparable statistic exists for a column type. `skipped` means the check could not
be computed, not that data is correct or incorrect. Do not treat it as a failure.

---

## Step 6 — Render the Validation Report

```python
from api_warehouse.report import render_validation

html = render_validation(result)
with open("validation.html", "w") as f:
    f.write(html)
print("Report written to validation.html")
```

`render_validation` accepts the dict returned by `reconcile` and writes a self-contained
HTML file with pass/fail/skipped rows colour-coded.

---

## Step 7 — Self-Check (Evals)

Before presenting results to the user, run the eval loop defined in
`../../references/running-evals.md` using the checks in `EVALS.md`. Spin up a grader
agent with a clean context, pass it `EVALS.md` and `validation.html`, and iterate until
every check is `pass` or `skipped` (or 5 rounds have elapsed). Report any remaining
failures plainly.

---

## Step 8 — Present Results

Tell the user the reconciliation summary:

> Validation complete.
> - **X** checks passed
> - **Y** checks failed
> - **Z** checks skipped (stat unavailable or types differ)
>
> Report saved to `validation.html`. Open it in a browser to inspect each check.

If checks **failed**: a row-count mismatch suggests an incomplete load or a pagination
gap. A numeric sum mismatch points to a transformation or rounding difference. A
timestamp range mismatch usually means timezone normalisation differs between source
and warehouse.

If checks are **skipped**: the comparison was not possible for those fields — data is
neither confirmed correct nor incorrect. Widening the sample or querying a full-table
count (if the source API supports it) may resolve some skips.

Do not claim completeness when checks are skipped.
