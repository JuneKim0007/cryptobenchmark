"""log/events.jsonl: every line JSON, schema 1, every field present with its type, a known kind; a line a crash cut
short is skipped, as every reader does (files.read_jsonl)."""
from __future__ import annotations

from pathlib import Path

from ..dto.event import FIELDS, KINDS, SCHEMA_VERSION
from ..files import read_jsonl


def _field_problems(doc: dict) -> list[str]:
    out = [f"missing {k}" for k in FIELDS if k not in doc]
    out += [f"unknown field {k}" for k in doc if k not in FIELDS]
    # bool is an int to isinstance; no field holds one
    out += [f"{k} is {type(doc[k]).__name__}" for k, types in FIELDS.items()
            if k in doc and (not isinstance(doc[k], types) or isinstance(doc[k], bool))]
    return out


def doc_problems(doc) -> list[str]:
    if not isinstance(doc, dict):
        return ["not an object"]
    if doc.get("schemaVersion") != SCHEMA_VERSION:
        return [f"schemaVersion {doc.get('schemaVersion')!r} is not {SCHEMA_VERSION}"]
    kind = [] if doc.get("kind") in KINDS else [f"kind {doc.get('kind')!r} is not one of {list(KINDS)}"]
    return _field_problems(doc) + kind


def validate_events(path: Path) -> list[str]:
    found = read_jsonl(path)
    out = [f"line {n}: does not parse: {e}" for n, e in found.bad]
    out += [f"line {n}: {p}" for n, doc in found.records for p in doc_problems(doc)]
    if found.partial:
        out.append(f"line {len(found.records) + len(found.cut) + len(found.bad) + 1}: partial, its writer stopped mid-line")
    return sorted(out, key=lambda p: int(p.split(":", 1)[0].split()[1]))
