"""log/events.jsonl: every line JSON, schema 1, every field present with its type, a known kind."""
from __future__ import annotations

import json
from pathlib import Path

from ..dto.event import FIELDS, KINDS, SCHEMA_VERSION


def _field_problems(doc: dict) -> list[str]:
    out = [f"missing {k}" for k in FIELDS if k not in doc]
    out += [f"unknown field {k}" for k in doc if k not in FIELDS]
    # bool is an int to isinstance; no field holds one
    out += [f"{k} is {type(doc[k]).__name__}" for k, types in FIELDS.items()
            if k in doc and (not isinstance(doc[k], types) or isinstance(doc[k], bool))]
    return out


def line_problems(line: str) -> list[str]:
    try:
        doc = json.loads(line)
    except ValueError as e:
        return [f"does not parse: {e}"]
    if not isinstance(doc, dict):
        return ["not an object"]
    if doc.get("schemaVersion") != SCHEMA_VERSION:
        return [f"schemaVersion {doc.get('schemaVersion')!r} is not {SCHEMA_VERSION}"]
    kind = [] if doc.get("kind") in KINDS else [f"kind {doc.get('kind')!r} is not one of {list(KINDS)}"]
    return _field_problems(doc) + kind


def validate_events(path: Path) -> list[str]:
    text = Path(path).read_text()
    lines = text.splitlines()
    out = [f"line {n}: {p}" for n, line in enumerate(lines, 1) for p in line_problems(line)]
    if text and not text.endswith("\n"):
        out.append(f"line {len(lines)}: partial, its writer stopped mid-line")
    return out
