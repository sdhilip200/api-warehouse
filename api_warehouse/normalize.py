"""Approximate dlt's default column-name normalization (camelCase -> snake_case)."""
from __future__ import annotations
import re

def to_snake_case(name: str) -> str:
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    return s.replace("-", "_").replace(" ", "_").lower()

def normalize_record_keys(records: list[dict]) -> list[dict]:
    """Rename each record's keys with to_snake_case so source records line up
    with dlt's loaded column names before profiling/reconciliation."""
    return [{to_snake_case(k): v for k, v in r.items()} for r in records]
