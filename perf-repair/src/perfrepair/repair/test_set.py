"""Candidates → a cryptobenchmark test set: every item an app runs, plus the members that could replace it."""
from __future__ import annotations

from ..dto.grouping import parse_qualified
from .candidates import Candidate


def build_test_set(found: list[Candidate], groups_doc: dict, app: str) -> dict:
    wanted = sorted({c.item for c in found} | {m for c in found for m in c.alternatives}, key=int)
    include = []
    for item in wanted:
        engine_type, name, provider = parse_qualified(groups_doc["items"][item]["qualified"])
        include.append({"provider": provider, "type": engine_type, "name": name})
    return {"schemaVersion": 1, "description": f"call sites of {app} and their replacements", "include": include}
