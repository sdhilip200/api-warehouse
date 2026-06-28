# api-warehouse Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `api-warehouse`, an MIT-licensed Claude Code plugin that takes any API's documentation and produces a client-ready assessment, sample data, a raw-landing dlt pipeline into a warehouse, a control-total validation report, and a deploy-ready bundle.

**Architecture:** The plugin is a set of agent **skills** (markdown `SKILL.md` files) that supply the *intelligence* (read docs → decide auth/pagination/incremental → orchestrate), plus a small, fully unit-tested Python support library `api_warehouse/` that supplies the *deterministic mechanics* (profile datasets, reconcile control totals, render HTML reports, build a dlt `rest_api` config). The skills call the library; **dlt** does the actual loading. Raw landing only — no transformation.

**Tech Stack:** Python 3.10+ · [dlt](https://github.com/dlt-hub/dlt) (`dlt[duckdb]` for tests, plus `bigquery`/`snowflake`/`postgres` extras) · pytest · DuckDB (zero-config local destination for the e2e test) · plain-Python HTML rendering (no template engine dependency).

## Global Constraints

- **License:** MIT, author GitHub `@sdhilip200`, repo `github.com/sdhilip200/api-warehouse`.
- **Python floor:** 3.10 (matches dlt's supported range 3.10–3.14).
- **Security (hard rule):** secrets are read only from environment variables or `.dlt/secrets.toml`; never hardcoded, never logged, never written into generated files, reports, or committed examples. Generated pipeline code references secrets by env-var name only.
- **Scope guard:** raw landing only. No transformation logic anywhere.
- **Destination connection:** dlt native connectors only — never MCP.
- **Honesty rule:** every report states confidence. Validation marks checks `skipped` when source-side data is unavailable; the incremental verdict is `YES (evidence)` / `NO (reason)`, never a bare guess.
- **Plugin shape:** `.claude-plugin/plugin.json` manifest + one `SKILL.md` per skill under `skills/`, mirroring compound-engineering-plugin and frontend-slides.
- **No external secret needed for tests:** the end-to-end test uses the public no-auth API `https://jsonplaceholder.typicode.com` into a local DuckDB file.

---

## File Structure

```
api-warehouse/
├── .claude-plugin/
│   └── plugin.json                     # plugin manifest (name, skills)
├── skills/
│   ├── api-warehouse/SKILL.md          # orchestrator: runs the full loop
│   ├── connect/SKILL.md                # secure auth setup + smoke test
│   ├── assess/SKILL.md                 # input guard, probe, incremental verdict, sample
│   ├── land/SKILL.md                   # destination + generate/run dlt pipeline
│   ├── validate/SKILL.md               # control-total reconciliation
│   └── schedule/SKILL.md               # deploy-ready bundle
├── references/
│   ├── security.md                     # secret-handling rules (linked by every skill)
│   ├── auth-patterns.md                # bearer/api-key/basic/oauth2 → dlt auth config
│   ├── pagination-patterns.md          # offset/page/cursor/link → dlt paginator config
│   ├── incremental-detection.md        # how to find + prove an incremental cursor
│   └── destinations.md                 # per-warehouse dlt setup + required env vars
├── api_warehouse/                      # tested Python support library
│   ├── __init__.py
│   ├── profile.py                      # dataset profiling (the basis of validation)
│   ├── reconcile.py                    # compare source vs loaded profiles
│   ├── report.py                       # JSON → standalone HTML reports
│   └── pipeline.py                     # endpoints-spec → dlt rest_api config
├── templates/
│   ├── Dockerfile                      # deploy bundle
│   └── deploy/                         # per-platform deploy instruction snippets
│       ├── cloud-run.md
│       ├── azure-container-apps.md
│       └── aws-ecs.md
├── examples/
│   └── jsonplaceholder/                # end-to-end worked example + screenshots
├── tests/
│   ├── test_profile.py
│   ├── test_reconcile.py
│   ├── test_report.py
│   ├── test_pipeline.py
│   ├── test_plugin_structure.py
│   └── test_e2e_jsonplaceholder.py     # real API → DuckDB → reconcile
├── .github/
│   ├── ISSUE_TEMPLATE/bug_report.md
│   ├── ISSUE_TEMPLATE/new_pattern.md
│   └── workflows/ci.yml
├── README.md
├── CONTRIBUTING.md
├── LICENSE
└── pyproject.toml
```

Build order: **scaffold → tested core library → e2e wiring → skills → references → docs/CI/example/deploy**. The library is built and tested first so the skills can reference concrete, working functions.

---

## Task 1: Repository scaffold, manifest, packaging

**Files:**
- Create: `pyproject.toml`
- Create: `.claude-plugin/plugin.json`
- Create: `api_warehouse/__init__.py`
- Create: `LICENSE`
- Create: `.gitignore`
- Test: `tests/test_plugin_structure.py`

**Interfaces:**
- Produces: an importable `api_warehouse` package; a parseable `plugin.json`; a pytest harness.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_plugin_structure.py
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def test_plugin_manifest_is_valid():
    manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "api-warehouse"
    assert isinstance(manifest.get("skills", []), list)

def test_package_imports():
    import api_warehouse
    assert api_warehouse.__version__
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_plugin_structure.py -v`
Expected: FAIL — `FileNotFoundError` / `ModuleNotFoundError`.

- [ ] **Step 3: Create the scaffold files**

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "api-warehouse"
version = "0.1.0"
description = "Any API docs -> assessment, sample data, and raw data landed in your warehouse."
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [{ name = "Dhilip Subramanian" }]
dependencies = ["dlt[duckdb]>=1.0"]

[project.optional-dependencies]
warehouses = ["dlt[bigquery,snowflake,postgres]>=1.0"]
dev = ["pytest>=8"]

[tool.setuptools]
packages = ["api_warehouse"]
```

```json
// .claude-plugin/plugin.json
{
  "name": "api-warehouse",
  "description": "Point a coding agent at any API's docs -> client-ready assessment, sample data, and raw data landed in your warehouse. Secure, validated, raw-landing only.",
  "version": "0.1.0",
  "author": { "name": "Dhilip Subramanian", "url": "https://github.com/sdhilip200" },
  "license": "MIT",
  "skills": [
    "skills/api-warehouse",
    "skills/connect",
    "skills/assess",
    "skills/land",
    "skills/validate",
    "skills/schedule"
  ]
}
```

```python
# api_warehouse/__init__.py
"""api-warehouse support library: profiling, reconciliation, reporting, dlt config."""
__version__ = "0.1.0"
```

```
# .gitignore
__pycache__/
*.pyc
.venv/
*.duckdb
.dlt/secrets.toml
/tmp_pipeline_data/
```

Create `LICENSE` as the standard MIT License text, copyright `2026 Dhilip Subramanian`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_plugin_structure.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .claude-plugin/plugin.json api_warehouse/__init__.py LICENSE .gitignore tests/test_plugin_structure.py
git commit -m "chore: scaffold api-warehouse plugin and package"
```

---

## Task 2: Dataset profiling (`api_warehouse/profile.py`)

**Files:**
- Create: `api_warehouse/profile.py`
- Test: `tests/test_profile.py`

**Interfaces:**
- Produces:
  - `classify_column(values: list) -> str` returning one of `"numeric" | "timestamp" | "text" | "empty"`.
  - `profile_records(records: list[dict]) -> dict` returning
    `{"row_count": int, "columns": {name: {...}}}` where each column dict has keys:
    `type`, `null_count`; numeric adds `sum`, `min`, `max`; timestamp adds `min`, `max`; text adds `distinct_count`, `top` (list of `[value, count]`, up to 5).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_profile.py
from api_warehouse.profile import classify_column, profile_records

def test_classify_numeric():
    assert classify_column([1, 2, 3.5, None]) == "numeric"

def test_classify_timestamp():
    assert classify_column(["2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z"]) == "timestamp"

def test_classify_text():
    assert classify_column(["a", "b", "a"]) == "text"

def test_classify_empty():
    assert classify_column([None, None]) == "empty"

def test_profile_records_counts_and_numeric_stats():
    rows = [
        {"id": 1, "amount": 10.0, "cat": "x", "ts": "2026-01-01T00:00:00Z"},
        {"id": 2, "amount": 30.0, "cat": "y", "ts": "2026-03-01T00:00:00Z"},
        {"id": 3, "amount": None, "cat": "x", "ts": None},
    ]
    p = profile_records(rows)
    assert p["row_count"] == 3
    amount = p["columns"]["amount"]
    assert amount["type"] == "numeric"
    assert amount["sum"] == 40.0
    assert amount["min"] == 10.0
    assert amount["max"] == 30.0
    assert amount["null_count"] == 1
    cat = p["columns"]["cat"]
    assert cat["type"] == "text"
    assert cat["distinct_count"] == 2
    assert ["x", 2] in cat["top"]
    ts = p["columns"]["ts"]
    assert ts["type"] == "timestamp"
    assert ts["min"] == "2026-01-01T00:00:00Z"
    assert ts["max"] == "2026-03-01T00:00:00Z"
    assert ts["null_count"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_profile.py -v`
Expected: FAIL — `ModuleNotFoundError: api_warehouse.profile`.

- [ ] **Step 3: Write minimal implementation**

```python
# api_warehouse/profile.py
"""Deterministic dataset profiling — the basis for control-total validation."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from numbers import Number


def _non_null(values: list) -> list:
    return [v for v in values if v is not None and v != ""]


def _is_number(v) -> bool:
    return isinstance(v, Number) and not isinstance(v, bool)


def _parse_ts(v):
    if not isinstance(v, str):
        return None
    text = v.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def classify_column(values: list) -> str:
    present = _non_null(values)
    if not present:
        return "empty"
    if all(_is_number(v) for v in present):
        return "numeric"
    if all(_parse_ts(v) is not None for v in present):
        return "timestamp"
    return "text"


def _column_values(records: list[dict], name: str) -> list:
    return [r.get(name) for r in records]


def profile_records(records: list[dict]) -> dict:
    columns: dict[str, dict] = {}
    names: list[str] = []
    for r in records:
        for k in r:
            if k not in columns:
                names.append(k)
                columns[k] = {}
    for name in names:
        values = _column_values(records, name)
        present = _non_null(values)
        null_count = len(values) - len(present)
        ctype = classify_column(values)
        info: dict = {"type": ctype, "null_count": null_count}
        if ctype == "numeric":
            info["sum"] = float(sum(present))
            info["min"] = float(min(present))
            info["max"] = float(max(present))
        elif ctype == "timestamp":
            parsed = sorted(present, key=_parse_ts)
            info["min"] = parsed[0]
            info["max"] = parsed[-1]
        elif ctype == "text":
            counts = Counter(str(v) for v in present)
            info["distinct_count"] = len(counts)
            info["top"] = [[v, c] for v, c in counts.most_common(5)]
        columns[name] = info
    return {"row_count": len(records), "columns": columns}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_profile.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add api_warehouse/profile.py tests/test_profile.py
git commit -m "feat: dataset profiling for control-total validation"
```

---

## Task 3: Control-total reconciliation (`api_warehouse/reconcile.py`)

**Files:**
- Create: `api_warehouse/reconcile.py`
- Test: `tests/test_reconcile.py`

**Interfaces:**
- Consumes: profile dicts from `profile_records` (Task 2).
- Produces:
  - `reconcile(source: dict, loaded: dict) -> dict` returning
    `{"checks": [ {"name": str, "kind": str, "status": "pass"|"fail"|"skipped", "detail": str} ], "ok": bool}`.
  - Rules: compare `row_count`; for each column present in both, compare by type — numeric `sum`/`min`/`max`, timestamp `min`/`max`, text `distinct_count`. A check is `skipped` when the column is missing on either side or types differ. `ok` is True when there are zero `fail` checks.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_reconcile.py
from api_warehouse.reconcile import reconcile

SOURCE = {
    "row_count": 3,
    "columns": {
        "amount": {"type": "numeric", "sum": 40.0, "min": 10.0, "max": 30.0, "null_count": 1},
        "cat": {"type": "text", "distinct_count": 2, "top": [["x", 2]], "null_count": 0},
        "only_source": {"type": "numeric", "sum": 1.0, "min": 1.0, "max": 1.0, "null_count": 0},
    },
}

def _loaded(**overrides):
    base = {
        "row_count": 3,
        "columns": {
            "amount": {"type": "numeric", "sum": 40.0, "min": 10.0, "max": 30.0, "null_count": 1},
            "cat": {"type": "text", "distinct_count": 2, "top": [["x", 2]], "null_count": 0},
        },
    }
    base.update(overrides)
    return base

def test_all_match_is_ok():
    result = reconcile(SOURCE, _loaded())
    assert result["ok"] is True
    statuses = {c["name"]: c["status"] for c in result["checks"]}
    assert statuses["row_count"] == "pass"
    assert statuses["amount.sum"] == "pass"

def test_row_count_mismatch_fails():
    result = reconcile(SOURCE, _loaded(row_count=2))
    assert result["ok"] is False
    assert any(c["name"] == "row_count" and c["status"] == "fail" for c in result["checks"])

def test_missing_column_is_skipped_not_failed():
    result = reconcile(SOURCE, _loaded())
    skipped = [c for c in result["checks"] if c["name"].startswith("only_source")]
    assert skipped and all(c["status"] == "skipped" for c in skipped)
    assert result["ok"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_reconcile.py -v`
Expected: FAIL — `ModuleNotFoundError: api_warehouse.reconcile`.

- [ ] **Step 3: Write minimal implementation**

```python
# api_warehouse/reconcile.py
"""Compare a source profile against a loaded profile -> control-total checks."""
from __future__ import annotations

_NUMERIC_FIELDS = ("sum", "min", "max")
_TIMESTAMP_FIELDS = ("min", "max")
_TEXT_FIELDS = ("distinct_count",)


def _check(name, kind, status, detail):
    return {"name": name, "kind": kind, "status": status, "detail": detail}


def reconcile(source: dict, loaded: dict) -> dict:
    checks: list[dict] = []

    s_rows, l_rows = source.get("row_count"), loaded.get("row_count")
    if s_rows is None or l_rows is None:
        checks.append(_check("row_count", "row_count", "skipped", "row count unavailable on one side"))
    else:
        status = "pass" if s_rows == l_rows else "fail"
        checks.append(_check("row_count", "row_count", status, f"source={s_rows} loaded={l_rows}"))

    s_cols = source.get("columns", {})
    l_cols = loaded.get("columns", {})
    for name in sorted(set(s_cols) | set(l_cols)):
        s, l = s_cols.get(name), l_cols.get(name)
        if s is None or l is None:
            checks.append(_check(f"{name}", "column", "skipped", "column missing on one side"))
            continue
        if s["type"] != l["type"]:
            checks.append(_check(f"{name}", "column", "skipped", f"type differs: {s['type']} vs {l['type']}"))
            continue
        fields = {"numeric": _NUMERIC_FIELDS, "timestamp": _TIMESTAMP_FIELDS, "text": _TEXT_FIELDS}.get(s["type"], ())
        if not fields:
            checks.append(_check(f"{name}", "column", "skipped", f"no comparable stat for type {s['type']}"))
            continue
        for f in fields:
            if f not in s or f not in l:
                checks.append(_check(f"{name}.{f}", s["type"], "skipped", "stat unavailable"))
                continue
            status = "pass" if s[f] == l[f] else "fail"
            checks.append(_check(f"{name}.{f}", s["type"], status, f"source={s[f]} loaded={l[f]}"))

    ok = all(c["status"] != "fail" for c in checks)
    return {"checks": checks, "ok": ok}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_reconcile.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add api_warehouse/reconcile.py tests/test_reconcile.py
git commit -m "feat: control-total reconciliation of source vs loaded data"
```

---

## Task 4: HTML reports (`api_warehouse/report.py`)

**Files:**
- Create: `api_warehouse/report.py`
- Test: `tests/test_report.py`

**Interfaces:**
- Consumes: an assessment dict (produced by the `assess` skill) and a reconcile result (Task 3).
- Produces:
  - `render_assessment(assessment: dict) -> str` — standalone HTML; must include the API name, the incremental verdict text, and a row per endpoint.
  - `render_validation(result: dict) -> str` — standalone HTML; one table row per check with its status; a summary line of pass/fail/skipped counts.
  - Both escape values with `html.escape` and return a full `<!doctype html>` document with inline CSS (zero external assets).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_report.py
from api_warehouse.report import render_assessment, render_validation

ASSESSMENT = {
    "api_name": "Demo API",
    "base_url": "https://api.demo.test",
    "incremental": {"supported": True, "evidence": "?updated_since= + updated_at field"},
    "endpoints": [
        {"name": "posts", "path": "/posts", "method": "GET", "primary_key": "id"},
    ],
}

def test_render_assessment_contains_key_facts():
    html = render_assessment(ASSESSMENT)
    assert "<!doctype html>" in html.lower()
    assert "Demo API" in html
    assert "updated_since" in html
    assert "/posts" in html

def test_render_validation_shows_statuses_and_summary():
    result = {
        "ok": False,
        "checks": [
            {"name": "row_count", "kind": "row_count", "status": "fail", "detail": "source=3 loaded=2"},
            {"name": "amount.sum", "kind": "numeric", "status": "pass", "detail": "source=40 loaded=40"},
            {"name": "x", "kind": "column", "status": "skipped", "detail": "missing"},
        ],
    }
    html = render_validation(result)
    assert "row_count" in html
    assert "fail" in html
    assert "1 passed" in html
    assert "1 failed" in html
    assert "1 skipped" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_report.py -v`
Expected: FAIL — `ModuleNotFoundError: api_warehouse.report`.

- [ ] **Step 3: Write minimal implementation**

```python
# api_warehouse/report.py
"""Render assessment and validation results as standalone, shareable HTML."""
from __future__ import annotations

from html import escape

_STYLE = """
<style>
 body{font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;margin:2rem auto;max-width:880px;color:#1a1a1a}
 h1{font-size:1.6rem} table{border-collapse:collapse;width:100%;margin:1rem 0}
 th,td{border:1px solid #ddd;padding:.5rem .6rem;text-align:left}
 th{background:#f5f5f5} .pass{color:#137333} .fail{color:#c5221f;font-weight:600} .skipped{color:#9aa0a6}
 .badge{display:inline-block;padding:.1rem .5rem;border-radius:.4rem;background:#eef}
</style>
"""


def _doc(title: str, body: str) -> str:
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{escape(title)}</title>{_STYLE}</head><body>{body}</body></html>"


def render_assessment(assessment: dict) -> str:
    name = escape(str(assessment.get("api_name", "API")))
    base = escape(str(assessment.get("base_url", "")))
    inc = assessment.get("incremental", {})
    verdict = "YES" if inc.get("supported") else "NO"
    evidence = escape(str(inc.get("evidence", "")))
    rows = ""
    for ep in assessment.get("endpoints", []):
        rows += (
            "<tr>"
            f"<td>{escape(str(ep.get('name','')))}</td>"
            f"<td>{escape(str(ep.get('method','GET')))}</td>"
            f"<td>{escape(str(ep.get('path','')))}</td>"
            f"<td>{escape(str(ep.get('primary_key','')))}</td>"
            "</tr>"
        )
    body = (
        f"<h1>API Assessment — {name}</h1>"
        f"<p>Base URL: <span class='badge'>{base}</span></p>"
        f"<p><strong>Incremental load:</strong> {verdict} &mdash; {evidence}</p>"
        "<h2>Endpoints</h2>"
        "<table><tr><th>Name</th><th>Method</th><th>Path</th><th>Primary key</th></tr>"
        f"{rows}</table>"
    )
    return _doc(f"API Assessment — {name}", body)


def render_validation(result: dict) -> str:
    checks = result.get("checks", [])
    passed = sum(1 for c in checks if c["status"] == "pass")
    failed = sum(1 for c in checks if c["status"] == "fail")
    skipped = sum(1 for c in checks if c["status"] == "skipped")
    rows = ""
    for c in checks:
        status = c["status"]
        rows += (
            "<tr>"
            f"<td>{escape(str(c['name']))}</td>"
            f"<td>{escape(str(c['kind']))}</td>"
            f"<td class='{status}'>{status}</td>"
            f"<td>{escape(str(c['detail']))}</td>"
            "</tr>"
        )
    summary = f"{passed} passed, {failed} failed, {skipped} skipped"
    body = (
        "<h1>Validation Report</h1>"
        f"<p><strong>{summary}</strong></p>"
        "<table><tr><th>Check</th><th>Kind</th><th>Status</th><th>Detail</th></tr>"
        f"{rows}</table>"
    )
    return _doc("Validation Report", body)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_report.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add api_warehouse/report.py tests/test_report.py
git commit -m "feat: standalone HTML assessment and validation reports"
```

---

## Task 5: dlt config builder (`api_warehouse/pipeline.py`)

**Files:**
- Create: `api_warehouse/pipeline.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: an `endpoints_spec` dict (produced by the `assess` skill, persisted as `endpoints.json`).
- Produces:
  - `build_rest_api_config(spec: dict, secrets: dict | None = None) -> dict` returning a dlt `rest_api` config dict with keys `client` (and `resources`).
  - Input spec shape:
    ```json
    {
      "base_url": "https://api.demo.test",
      "auth": {"type": "none"} | {"type": "bearer", "token_env": "API_TOKEN"} | {"type": "api_key", "name": "X-Key", "location": "header", "token_env": "API_KEY"},
      "paginator": {"type": "single_page"} | {"type": "page_number", "base_page": 1, "total_path": null} | {"type": "offset", "limit": 100} | {"type": "json_link", "next_url_path": "next"},
      "resources": [
        {"name": "posts", "path": "/posts", "primary_key": "id",
         "incremental": null | {"cursor_path": "updated_at", "param": "updated_since", "initial_value": "2020-01-01"}}
      ]
    }
    ```
  - Rules: `auth.type == "none"` → no `auth` key. `bearer` → `{"type":"bearer","token": secrets[token_env]}`. `api_key` → `{"type":"api_key","name":..., "location":..., "api_key": secrets[token_env]}`. Resource `write_disposition` is `"merge"` when `incremental` is set (with `primary_key`), else `"replace"`. Incremental adds `endpoint.incremental` `{cursor_path, initial_value}` and maps `param` into `endpoint.params[param]` as `"{incremental.start_value}"`.
  - Raises `KeyError` if a referenced secret env name is missing from `secrets`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_pipeline.py
import pytest
from api_warehouse.pipeline import build_rest_api_config

def test_no_auth_single_page_replace():
    spec = {
        "base_url": "https://api.demo.test",
        "auth": {"type": "none"},
        "paginator": {"type": "single_page"},
        "resources": [{"name": "posts", "path": "/posts", "primary_key": "id", "incremental": None}],
    }
    cfg = build_rest_api_config(spec)
    assert cfg["client"]["base_url"] == "https://api.demo.test"
    assert "auth" not in cfg["client"]
    res = cfg["resources"][0]
    assert res["name"] == "posts"
    assert res["endpoint"]["path"] == "/posts"
    assert res["write_disposition"] == "replace"

def test_bearer_auth_reads_secret():
    spec = {
        "base_url": "https://api.demo.test",
        "auth": {"type": "bearer", "token_env": "API_TOKEN"},
        "paginator": {"type": "page_number", "base_page": 1, "total_path": None},
        "resources": [{"name": "orders", "path": "/orders", "primary_key": "id", "incremental": None}],
    }
    cfg = build_rest_api_config(spec, secrets={"API_TOKEN": "abc123"})
    assert cfg["client"]["auth"] == {"type": "bearer", "token": "abc123"}

def test_incremental_sets_merge_and_params():
    spec = {
        "base_url": "https://api.demo.test",
        "auth": {"type": "none"},
        "paginator": {"type": "single_page"},
        "resources": [{
            "name": "events", "path": "/events", "primary_key": "id",
            "incremental": {"cursor_path": "updated_at", "param": "updated_since", "initial_value": "2020-01-01"},
        }],
    }
    cfg = build_rest_api_config(spec)
    res = cfg["resources"][0]
    assert res["write_disposition"] == "merge"
    assert res["endpoint"]["incremental"]["cursor_path"] == "updated_at"
    assert res["endpoint"]["incremental"]["initial_value"] == "2020-01-01"
    assert res["endpoint"]["params"]["updated_since"] == "{incremental.start_value}"

def test_missing_secret_raises():
    spec = {
        "base_url": "https://api.demo.test",
        "auth": {"type": "bearer", "token_env": "API_TOKEN"},
        "paginator": {"type": "single_page"},
        "resources": [{"name": "x", "path": "/x", "primary_key": "id", "incremental": None}],
    }
    with pytest.raises(KeyError):
        build_rest_api_config(spec, secrets={})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipeline.py -v`
Expected: FAIL — `ModuleNotFoundError: api_warehouse.pipeline`.

- [ ] **Step 3: Write minimal implementation**

```python
# api_warehouse/pipeline.py
"""Turn an assess-produced endpoints spec into a dlt rest_api config dict."""
from __future__ import annotations


def _auth(spec_auth: dict, secrets: dict) -> dict | None:
    kind = spec_auth.get("type", "none")
    if kind == "none":
        return None
    if kind == "bearer":
        return {"type": "bearer", "token": secrets[spec_auth["token_env"]]}
    if kind == "api_key":
        return {
            "type": "api_key",
            "name": spec_auth["name"],
            "location": spec_auth.get("location", "header"),
            "api_key": secrets[spec_auth["token_env"]],
        }
    raise ValueError(f"unsupported auth type: {kind}")


def _resource(r: dict) -> dict:
    endpoint: dict = {"path": r["path"]}
    incremental = r.get("incremental")
    if incremental:
        endpoint["incremental"] = {
            "cursor_path": incremental["cursor_path"],
            "initial_value": incremental.get("initial_value"),
        }
        endpoint.setdefault("params", {})[incremental["param"]] = "{incremental.start_value}"
        write_disposition = "merge"
    else:
        write_disposition = "replace"
    return {
        "name": r["name"],
        "endpoint": endpoint,
        "primary_key": r.get("primary_key"),
        "write_disposition": write_disposition,
    }


def build_rest_api_config(spec: dict, secrets: dict | None = None) -> dict:
    secrets = secrets or {}
    client: dict = {"base_url": spec["base_url"]}
    auth = _auth(spec.get("auth", {"type": "none"}), secrets)
    if auth is not None:
        client["auth"] = auth
    paginator = spec.get("paginator")
    if paginator and paginator.get("type") != "single_page":
        client["paginator"] = paginator
    return {"client": client, "resources": [_resource(r) for r in spec["resources"]]}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_pipeline.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add api_warehouse/pipeline.py tests/test_pipeline.py
git commit -m "feat: build dlt rest_api config from endpoints spec"
```

---

## Task 6: End-to-end test — real API → DuckDB → reconcile

**Files:**
- Create: `tests/test_e2e_jsonplaceholder.py`

**Interfaces:**
- Consumes: `build_rest_api_config` (Task 5), `profile_records` (Task 2), `reconcile` (Task 3), and dlt's `rest_api_source` + `dlt.pipeline`.
- Produces: proof that a generated config loads a real public API into DuckDB and reconciles. This is the integration test that anchors the whole library.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_e2e_jsonplaceholder.py
"""End-to-end: JSONPlaceholder /posts -> DuckDB -> reconcile. Requires network."""
import urllib.request
import json
import pytest

duckdb = pytest.importorskip("duckdb")
dlt = pytest.importorskip("dlt")
from dlt.sources.rest_api import rest_api_source  # noqa: E402

from api_warehouse.pipeline import build_rest_api_config
from api_warehouse.profile import profile_records
from api_warehouse.reconcile import reconcile

BASE = "https://jsonplaceholder.typicode.com"

def _fetch_source_posts():
    with urllib.request.urlopen(f"{BASE}/posts", timeout=30) as resp:
        return json.loads(resp.read().decode())

def test_load_posts_into_duckdb_and_reconcile(tmp_path):
    source_records = _fetch_source_posts()
    assert len(source_records) == 100  # sanity: API shape unchanged

    spec = {
        "base_url": BASE,
        "auth": {"type": "none"},
        "paginator": {"type": "single_page"},
        "resources": [{"name": "posts", "path": "/posts", "primary_key": "id", "incremental": None}],
    }
    config = build_rest_api_config(spec)
    source = rest_api_source(config)

    db_path = tmp_path / "warehouse.duckdb"
    pipeline = dlt.pipeline(
        pipeline_name="api_warehouse_e2e",
        destination=dlt.destinations.duckdb(str(db_path)),
        dataset_name="raw",
    )
    pipeline.run(source)

    con = duckdb.connect(str(db_path))
    loaded_rows = [
        dict(zip([c[0] for c in con.description], row))
        for row in con.execute("SELECT id, user_id, title FROM raw.posts").fetchall()
    ]
    con.close()

    src_profile = profile_records([
        {"id": r["id"], "user_id": r["userId"], "title": r["title"]} for r in source_records
    ])
    loaded_profile = profile_records(loaded_rows)
    result = reconcile(src_profile, loaded_profile)

    assert result["ok"] is True, result["checks"]
    assert src_profile["row_count"] == loaded_profile["row_count"] == 100
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_e2e_jsonplaceholder.py -v`
Expected: FAIL initially if `dlt[duckdb]` isn't installed — install with `pip install -e ".[dev]"` then re-run. Expected after install: PASS. If the dlt `rest_api` config shape needs a tweak for the installed dlt version, adjust `build_rest_api_config` and its unit tests together, keeping Task 5's tests green.

- [ ] **Step 3: Make it pass**

Run: `pip install -e ".[dev]"` then `pytest tests/test_e2e_jsonplaceholder.py -v`
Expected: PASS (1 passed). If column name casing differs (dlt normalizes `userId` → `user_id`), the SELECT above already uses `user_id`; keep it aligned with dlt's normalized names.

- [ ] **Step 4: Run the full suite**

Run: `pytest -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/test_e2e_jsonplaceholder.py
git commit -m "test: end-to-end JSONPlaceholder -> DuckDB -> reconcile"
```

---

## Task 7: Reference docs (`references/`)

**Files:**
- Create: `references/security.md`
- Create: `references/auth-patterns.md`
- Create: `references/pagination-patterns.md`
- Create: `references/incremental-detection.md`
- Create: `references/destinations.md`
- Test: extend `tests/test_plugin_structure.py`

**Interfaces:**
- Produces: the shared knowledge each skill links to. These keep skill bodies short and let contributors add patterns without touching skill logic.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_plugin_structure.py
REFERENCES = ["security", "auth-patterns", "pagination-patterns", "incremental-detection", "destinations"]

def test_reference_docs_exist_and_nonempty():
    for ref in REFERENCES:
        p = ROOT / "references" / f"{ref}.md"
        assert p.exists(), f"missing reference: {ref}"
        assert len(p.read_text().strip()) > 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_plugin_structure.py::test_reference_docs_exist_and_nonempty -v`
Expected: FAIL — missing references.

- [ ] **Step 3: Write the reference docs**

Create `references/security.md` covering: read secrets only from env vars / `.dlt/secrets.toml`; never print, log, or write secret values into reports or generated code; generated pipelines reference secrets by env-var name only; scrub example data of tokens; tell the user the exact `export VAR=...` and `secrets.toml` snippet to set, but never store the value yourself.

Create `references/auth-patterns.md` mapping each auth style to a `pipeline.build_rest_api_config` `auth` spec:
- None → `{"type": "none"}`
- Bearer token → `{"type": "bearer", "token_env": "API_TOKEN"}`
- API key (header or query) → `{"type": "api_key", "name": "X-API-Key", "location": "header"|"query", "token_env": "API_KEY"}`
- Basic auth → document as bearer-of-base64 or direct dlt `HttpBasicAuth`; note OAuth2 client-credentials as a documented manual step (obtain token out-of-band, supply as bearer) for v1.

Create `references/pagination-patterns.md` mapping detection cues to paginator specs: page-number (`?page=`), offset/limit (`?offset=&limit=`), cursor/next-token (response `next`/`cursor`), link header / `json_link` (response field with next URL), and single-page (no pagination). Each entry shows the exact `paginator` dict for the spec.

Create `references/incremental-detection.md`: the senior-DE checklist — look for `updated_since`/`modified_after`/`since`/`start_date` query params; sortable `updated_at`/`modified_at` response fields; cursors/change-feeds/webhooks. Define the verdict format: `{"supported": true, "evidence": "..."}` or `{"supported": false, "reason": "..."}`. State the rule: never claim incremental without a named param or cursor field as evidence.

Create `references/destinations.md`: per-destination dlt setup and required env vars — DuckDB (local, zero-config, for testing), Postgres, BigQuery (service-account JSON), Snowflake, Azure SQL, and blob (filesystem destination, Parquet/CSV). For each: the `dlt` destination call and the exact secret env names, with a note that none are hardcoded.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_plugin_structure.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add references/ tests/test_plugin_structure.py
git commit -m "docs: reference patterns for auth, pagination, incremental, destinations, security"
```

---

## Task 8: `connect` skill

**Files:**
- Create: `skills/connect/SKILL.md`
- Test: extend `tests/test_plugin_structure.py`

**Interfaces:**
- Produces: the skill that sets up secure auth and runs a smoke test. Later skills assume a working, env-var-based credential and a reachable API.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_plugin_structure.py
SKILLS = ["api-warehouse", "connect", "assess", "land", "validate", "schedule"]

def _frontmatter(path):
    text = path.read_text()
    assert text.startswith("---"), f"{path} missing frontmatter"
    fm = text.split("---", 2)[1]
    return fm

def test_connect_skill_present_with_frontmatter():
    p = ROOT / "skills" / "connect" / "SKILL.md"
    assert p.exists()
    fm = _frontmatter(p)
    assert "name:" in fm and "description:" in fm
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_plugin_structure.py::test_connect_skill_present_with_frontmatter -v`
Expected: FAIL — file missing.

- [ ] **Step 3: Write the skill**

Create `skills/connect/SKILL.md` with frontmatter `name: connect`, a `description` that triggers on "connect to an API / set up API auth / test API credentials", and a body that:
1. Reads `references/security.md` and follows it strictly.
2. Determines auth type from the docs (link to `references/auth-patterns.md`).
3. Instructs the user to set the credential as an environment variable (show the exact `export NAME=value` and `.dlt/secrets.toml` form) — **never** asks them to paste the secret into chat, never stores it.
4. Runs a single minimal authenticated request as a smoke test.
5. Reports: reachable? auth valid? rate-limit headers seen? — in plain language. On failure, gives the specific next step.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_plugin_structure.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/connect/SKILL.md tests/test_plugin_structure.py
git commit -m "feat: connect skill — secure auth setup + smoke test"
```

---

## Task 9: `assess` skill

**Files:**
- Create: `skills/assess/SKILL.md`
- Test: extend `tests/test_plugin_structure.py`

**Interfaces:**
- Consumes: a reachable API from `connect`; `references/*`.
- Produces: `assessment.html` (via `api_warehouse.report.render_assessment`), `endpoints.json` (the spec consumed by `pipeline.build_rest_api_config`), and `samples/`. The `endpoints.json` MUST match the spec shape in Task 5.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_plugin_structure.py
def test_assess_skill_present():
    p = ROOT / "skills" / "assess" / "SKILL.md"
    assert p.exists()
    body = p.read_text()
    assert "endpoints.json" in body
    assert "not API documentation" in body  # input guard wording present
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_plugin_structure.py::test_assess_skill_present -v`
Expected: FAIL — file missing.

- [ ] **Step 3: Write the skill**

Create `skills/assess/SKILL.md` (frontmatter `name: assess`, description triggering on "assess an API / read API docs / build API assessment"). Body, in order:
1. **Input guard (Step 0):** confirm the input is genuinely API documentation (endpoints, methods, auth visible). If not, STOP and say *"This doesn't look like API documentation — I can't find endpoints, methods, or auth. Did you mean a different link?"*
2. **Endpoint inventory:** list endpoints, methods, params, response fields/types.
3. **Capabilities:** pagination (link `references/pagination-patterns.md`), rate limits, auth (link `references/auth-patterns.md`).
4. **Incremental verdict:** follow `references/incremental-detection.md`; produce `{"supported": bool, "evidence"|"reason": str}` — never guess without evidence.
5. **Intent interview:** ask how much data, and one-time raw vs incremental; reconcile the user's wish against the incremental verdict.
6. **Sample pull:** fetch a few real rows per key endpoint into `samples/`.
7. **Write artifacts:** assemble the assessment dict and `endpoints.json` (exact shape from Task 5), then render `assessment.html` with `api_warehouse.report.render_assessment`.
8. **Checkpoint:** tell the user to read `assessment.html` and confirm scope / get client sign-off before `land`.

Include a literal `endpoints.json` example block matching Task 5's spec shape.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_plugin_structure.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/assess/SKILL.md tests/test_plugin_structure.py
git commit -m "feat: assess skill — input guard, probe, incremental verdict, sample"
```

---

## Task 10: `land` skill

**Files:**
- Create: `skills/land/SKILL.md`
- Test: extend `tests/test_plugin_structure.py`

**Interfaces:**
- Consumes: `endpoints.json` from `assess`; a chosen destination; secrets from env/`secrets.toml`.
- Produces: a committed dlt pipeline script in the user's project + raw data in the destination.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_plugin_structure.py
def test_land_skill_present():
    p = ROOT / "skills" / "land" / "SKILL.md"
    assert p.exists()
    body = p.read_text()
    assert "build_rest_api_config" in body
    assert "destinations.md" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_plugin_structure.py::test_land_skill_present -v`
Expected: FAIL — file missing.

- [ ] **Step 3: Write the skill**

Create `skills/land/SKILL.md` (frontmatter `name: land`, description triggering on "load API data / land raw data / build dlt pipeline"). Body:
1. Ask for the destination; link `references/destinations.md` for the exact dlt destination call and required env vars.
2. Confirm secrets are set as env vars (never paste in chat) per `references/security.md`.
3. Generate a small, readable pipeline script that calls `api_warehouse.pipeline.build_rest_api_config(spec, secrets)` with `spec` loaded from `endpoints.json`, wraps it in `dlt.sources.rest_api.rest_api_source`, and runs `dlt.pipeline(...).run(...)` into the chosen destination with `dataset_name="raw"`. Raw landing only — no transformation.
4. Show the generated script to the user, run it, and report rows loaded per resource.

Include the literal generated-script template (no-auth and bearer variants), reading secrets via `os.environ`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_plugin_structure.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/land/SKILL.md tests/test_plugin_structure.py
git commit -m "feat: land skill — generate and run dlt raw-landing pipeline"
```

---

## Task 11: `validate` skill

**Files:**
- Create: `skills/validate/SKILL.md`
- Test: extend `tests/test_plugin_structure.py`

**Interfaces:**
- Consumes: source samples + loaded data; `api_warehouse.profile`, `api_warehouse.reconcile`, `api_warehouse.report.render_validation`.
- Produces: `validation.html`.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_plugin_structure.py
def test_validate_skill_present():
    p = ROOT / "skills" / "validate" / "SKILL.md"
    assert p.exists()
    body = p.read_text()
    assert "render_validation" in body
    assert "skipped" in body  # honesty about unavailable checks
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_plugin_structure.py::test_validate_skill_present -v`
Expected: FAIL — file missing.

- [ ] **Step 3: Write the skill**

Create `skills/validate/SKILL.md` (frontmatter `name: validate`, description triggering on "validate loaded data / reconcile API vs warehouse / control totals"). Body:
1. Fetch a source-side dataset (re-pull from API, bounded) and query the loaded warehouse table.
2. Profile both with `api_warehouse.profile.profile_records`.
3. Reconcile with `api_warehouse.reconcile.reconcile`.
4. Render `validation.html` with `api_warehouse.report.render_validation`.
5. State honestly when source counts/stats are unavailable (checks come back `skipped`) — validation is best-effort; never claim an exact match that wasn't computed.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_plugin_structure.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/validate/SKILL.md tests/test_plugin_structure.py
git commit -m "feat: validate skill — best-effort control-total reconciliation"
```

---

## Task 12: `schedule` skill + deploy templates

**Files:**
- Create: `skills/schedule/SKILL.md`
- Create: `templates/Dockerfile`
- Create: `templates/deploy/cloud-run.md`
- Create: `templates/deploy/azure-container-apps.md`
- Create: `templates/deploy/aws-ecs.md`
- Test: extend `tests/test_plugin_structure.py`

**Interfaces:**
- Consumes: the generated pipeline script from `land`.
- Produces: a deploy-ready bundle (Dockerfile + schedule config + per-platform instructions). v1 does NOT auto-deploy.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_plugin_structure.py
def test_schedule_skill_and_templates_present():
    assert (ROOT / "skills" / "schedule" / "SKILL.md").exists()
    df = (ROOT / "templates" / "Dockerfile").read_text()
    assert "python" in df.lower()
    for plat in ["cloud-run", "azure-container-apps", "aws-ecs"]:
        assert (ROOT / "templates" / "deploy" / f"{plat}.md").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_plugin_structure.py::test_schedule_skill_and_templates_present -v`
Expected: FAIL — files missing.

- [ ] **Step 3: Write the skill and templates**

Create `templates/Dockerfile`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Secrets are provided at runtime via environment variables — never baked into the image.
CMD ["python", "pipeline.py"]
```

Create the three `templates/deploy/*.md` files with copy-paste instructions: build/push the image, set secrets as the platform's managed env vars/secrets, and create a scheduled trigger (Cloud Run Job + Cloud Scheduler; Azure Container Apps Job with cron; AWS ECS scheduled task / EventBridge). Each emphasizes: secrets via the platform's secret manager, never in the image.

Create `skills/schedule/SKILL.md` (frontmatter `name: schedule`, description triggering on "schedule the pipeline / deploy the pipeline / run on a cron"). Body: ask which platform; copy the `Dockerfile`, a `requirements.txt`, and the platform's deploy doc into a `deploy/` bundle in the user's project; fill in the schedule (cron) the user wants; explicitly tell the user this produces a deploy-ready bundle that **they** run — v1 does not push to their cloud.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_plugin_structure.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/schedule/SKILL.md templates/ tests/test_plugin_structure.py
git commit -m "feat: schedule skill + deploy-ready bundle templates"
```

---

## Task 13: `api-warehouse` orchestrator skill

**Files:**
- Create: `skills/api-warehouse/SKILL.md`
- Test: extend `tests/test_plugin_structure.py`

**Interfaces:**
- Consumes: the five step-skills.
- Produces: a single entry point running `connect → assess → [checkpoint] → land → validate → schedule`.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_plugin_structure.py
def test_orchestrator_lists_full_loop():
    body = (ROOT / "skills" / "api-warehouse" / "SKILL.md").read_text()
    for step in ["connect", "assess", "land", "validate", "schedule"]:
        assert step in body
    assert "checkpoint" in body.lower()

def test_all_skills_have_unique_names():
    import re
    names = []
    for s in SKILLS:
        fm = _frontmatter(ROOT / "skills" / s / "SKILL.md")
        m = re.search(r"name:\s*(\S+)", fm)
        names.append(m.group(1))
    assert len(names) == len(set(names))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_plugin_structure.py -v`
Expected: FAIL — orchestrator missing.

- [ ] **Step 3: Write the skill**

Create `skills/api-warehouse/SKILL.md` (frontmatter `name: api-warehouse`, description triggering on "ingest an API end to end / API to warehouse / build an ingestion pipeline from API docs"). Body: explain the loop, then run each step skill in order, pausing at the **checkpoint** after `assess` for the user to read `assessment.html` and confirm scope / client sign-off before `land`. State the scope guard (raw landing only) and the security rule up front.

- [ ] **Step 4: Run full suite**

Run: `pytest -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add skills/api-warehouse/SKILL.md tests/test_plugin_structure.py
git commit -m "feat: orchestrator skill — full connect->...->schedule loop"
```

---

## Task 14: README, CONTRIBUTING, worked example, CI

**Files:**
- Create: `README.md`
- Create: `CONTRIBUTING.md`
- Create: `examples/jsonplaceholder/README.md`
- Create: `.github/ISSUE_TEMPLATE/bug_report.md`
- Create: `.github/ISSUE_TEMPLATE/new_pattern.md`
- Create: `.github/workflows/ci.yml`
- Test: extend `tests/test_plugin_structure.py`

**Interfaces:**
- Produces: the professional GitHub presentation (the star-driver) and CI that runs the test suite.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_plugin_structure.py
def test_readme_has_install_and_positioning():
    r = (ROOT / "README.md").read_text()
    assert "/plugin marketplace add https://github.com/sdhilip200/api-warehouse" in r
    assert "dlt" in r and "printing-press" in r  # honest positioning section
    assert (ROOT / "CONTRIBUTING.md").exists()
    assert (ROOT / ".github" / "workflows" / "ci.yml").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_plugin_structure.py::test_readme_has_install_and_positioning -v`
Expected: FAIL.

- [ ] **Step 3: Write the docs and CI**

`README.md` — open with the one-line pitch; a "paste any API docs → assessment + loaded data" demo placeholder for a GIF; **Quick start** (`/plugin marketplace add https://github.com/sdhilip200/api-warehouse` then `/plugin install`); the **loop** diagram; the honest **positioning table** vs dlt and printing-press (from the spec §2); the **security** promise; **scope guard** (raw landing only); link to the worked example; MIT + author `@sdhilip200`; badges (CI, license).

`CONTRIBUTING.md` — how to add a new pattern (a new entry in `references/pagination-patterns.md` / `auth-patterns.md` / `destinations.md`) or a new skill; how to run tests (`pip install -e ".[dev]" && pytest`); the security and honesty rules as contribution requirements; PR checklist.

`examples/jsonplaceholder/README.md` — the end-to-end walkthrough mirroring the e2e test: assess JSONPlaceholder, land `/posts` into DuckDB/Postgres, validate, with the expected report outputs described.

`.github/ISSUE_TEMPLATE/new_pattern.md` — template for proposing a new auth/pagination/destination pattern.
`.github/ISSUE_TEMPLATE/bug_report.md` — standard bug template.

`.github/workflows/ci.yml`:

```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: pytest -v
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add README.md CONTRIBUTING.md examples/ .github/ tests/test_plugin_structure.py
git commit -m "docs: README, CONTRIBUTING, worked example, and CI"
```

---

## Self-Review (completed against the spec)

**Spec coverage:**
- §2 positioning vs dlt/printing-press → Task 14 (README) + asserted in test.
- §3 goals (human docs, runtime-adaptive, security, honesty) → assess (Task 9), connect (Task 8), security.md (Task 7).
- §3 non-goals (no transformation, no auto-deploy, no MCP) → enforced in land (Task 10), schedule (Task 12), destinations.md (Task 7), Global Constraints.
- §5 architecture / plugin shape → Task 1 manifest + Tasks 8–13 skills.
- §6.1 connect → Task 8. §6.2 assess (guard, incremental verdict, intent, sample) → Task 9. §6.3 land → Task 10. §6.4 validate (control totals) → Tasks 2,3,4,11. §6.5 schedule (option A) → Task 12. §6.6 orchestrator → Task 13.
- §7 security model → Task 7 security.md + referenced by Tasks 8,10.
- §8 HTML reports → Task 4 + 11.
- §9 professional GitHub → Task 14.
- §11 success criteria (paste docs → assessment+sample+land+validate; evidence-backed incremental; reject non-API input; secrets never leak) → e2e (Task 6) + assess guard (Task 9) + security (Task 7).

**Placeholder scan:** No "TBD"/"handle edge cases" in code steps; library tasks contain full implementations and tests. Skill/reference/doc tasks specify exact required content and are gated by structural tests asserting the load-bearing strings.

**Type consistency:** `profile_records` output shape is consumed unchanged by `reconcile` (Task 3) and the e2e (Task 6). `build_rest_api_config(spec, secrets)` signature and the `endpoints.json` spec shape are identical across Tasks 5, 6, 9, 10. `render_assessment`/`render_validation` names match across Tasks 4, 9, 11.

**Known follow-up:** the exact dlt `rest_api` config keys may need a minor version-specific tweak; Task 6 explicitly instructs adjusting `build_rest_api_config` and its unit tests together if so. This is the one place reality (installed dlt version) must be reconciled during execution.
