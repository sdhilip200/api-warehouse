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
