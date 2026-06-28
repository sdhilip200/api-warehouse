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

def test_render_assessment_shows_reason_when_not_supported():
    a = {"api_name": "X", "base_url": "u", "incremental": {"supported": False, "reason": "no timestamp fields"}, "endpoints": []}
    html = render_assessment(a)
    assert "NO" in html
    assert "no timestamp fields" in html

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
