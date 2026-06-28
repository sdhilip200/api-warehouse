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

def test_api_key_auth():
    spec = {
        "base_url": "https://api.demo.test",
        "auth": {"type": "api_key", "name": "X-API-Key", "location": "header", "token_env": "API_KEY"},
        "paginator": {"type": "single_page"},
        "resources": [{"name": "items", "path": "/items", "primary_key": "id", "incremental": None}],
    }
    cfg = build_rest_api_config(spec, secrets={"API_KEY": "k"})
    assert cfg["client"]["auth"] == {"type": "api_key", "name": "X-API-Key", "location": "header", "api_key": "k"}

def test_missing_secret_raises():
    spec = {
        "base_url": "https://api.demo.test",
        "auth": {"type": "bearer", "token_env": "API_TOKEN"},
        "paginator": {"type": "single_page"},
        "resources": [{"name": "x", "path": "/x", "primary_key": "id", "incremental": None}],
    }
    with pytest.raises(KeyError):
        build_rest_api_config(spec, secrets={})
