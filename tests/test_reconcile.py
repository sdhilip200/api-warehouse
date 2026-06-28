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
