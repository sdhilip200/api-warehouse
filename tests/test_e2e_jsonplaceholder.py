# tests/test_e2e_jsonplaceholder.py
"""End-to-end: JSONPlaceholder /posts -> DuckDB -> reconcile. Requires network."""
import urllib.request
import json
import ssl
import pytest

duckdb = pytest.importorskip("duckdb")
dlt = pytest.importorskip("dlt")
from dlt.sources.rest_api import rest_api_source  # noqa: E402

from api_warehouse.pipeline import build_rest_api_config
from api_warehouse.profile import profile_records
from api_warehouse.reconcile import reconcile

BASE = "https://jsonplaceholder.typicode.com"

def _fetch_source_posts():
    ctx = ssl.create_default_context()
    try:
        import certifi
        ctx.load_verify_locations(certifi.where())
    except ImportError:
        pass
    with urllib.request.urlopen(f"{BASE}/posts", timeout=30, context=ctx) as resp:
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
