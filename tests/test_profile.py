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
