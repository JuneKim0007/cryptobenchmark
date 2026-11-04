"""log/details/benchmark_coverage.yaml: its schema, run and point; each gap a known class with its action and a reason."""
from __future__ import annotations

from ..dto.benchmark_coverage import ACTIONS, CLASSES, MEASURED, POINTS, SCHEMA_VERSION


def _gap(where: str, g: dict) -> list[str]:
    out = [] if g.get("gap") in CLASSES else [f"{where}: gap {g.get('gap')!r} is not one of {list(CLASSES)}"]
    if g.get("gap") in CLASSES and g.get("action") != ACTIONS[g["gap"]]:
        out.append(f"{where}: action {g.get('action')!r} is not {ACTIONS[g['gap']]!r}, the {g['gap']} class's")
    if not g.get("item") or not g.get("reason") or not g.get("metric"):
        out.append(f"{where}: no item, metric or reason")
    return out


def validate_coverage(doc: dict) -> list[str]:
    if doc.get("schemaVersion") != SCHEMA_VERSION:
        return [f"schemaVersion is not {SCHEMA_VERSION}"]
    out = [] if doc.get("run") else ["no run id"]
    if doc.get("point") not in POINTS:
        out.append(f"point {doc.get('point')!r} is not one of {list(POINTS)}")
    statuses = set((doc.get("items") or {}).values()) - {MEASURED, *CLASSES}
    if statuses:
        out.append(f"items hold unknown statuses {sorted(statuses)}")
    return out + [p for i, g in enumerate(doc.get("gaps") or []) for p in _gap(f"gaps[{i}]", g)]
