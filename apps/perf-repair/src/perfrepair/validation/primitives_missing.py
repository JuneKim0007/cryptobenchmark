"""log/details/primitives_missing.yaml: its schema and run; each row a known reason and action, its lists, a next step."""
from __future__ import annotations

from ..dto.primitives_missing import ACTIONS, REASONS, SCHEMA_VERSION


def _row(where: str, r: dict) -> list[str]:
    out = [] if r.get("primitive") or r.get("provider") else [f"{where}: neither a primitive nor a provider"]
    if r.get("reason") not in REASONS:
        out.append(f"{where}: reason {r.get('reason')!r} is not one of {list(REASONS)}")
    if r.get("action") not in ACTIONS:
        out.append(f"{where}: action {r.get('action')!r} is not one of {list(ACTIONS)}")
    if not isinstance(r.get("apps"), list) or not isinstance(r.get("coordinates"), list):
        out.append(f"{where}: apps and coordinates are lists")
    if not isinstance(r.get("sites"), int) or not r.get("next"):
        out.append(f"{where}: no site count or next step")
    return out


def validate_missing(doc: dict) -> list[str]:
    if doc.get("schemaVersion") != SCHEMA_VERSION:
        return [f"schemaVersion is not {SCHEMA_VERSION}"]
    out = [] if doc.get("run") else ["no run id"]
    rows = doc.get("missing")
    if not isinstance(rows, list):
        return [*out, "missing is not a list"]
    return out + [p for i, r in enumerate(rows) for p in _row(f"missing[{i}]", r)]
