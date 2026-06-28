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
            f"<td class='{escape(status)}'>{escape(status)}</td>"
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
