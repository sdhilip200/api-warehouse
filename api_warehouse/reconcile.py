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
