"""dossiers.json → a cryptobenchmark test set: each scope's current item and every option, nothing else."""
from __future__ import annotations

from ..dto.dossier import Dossier
from ..dto.grouping import parse_qualified


def build_test_set(doc: dict, app: str) -> dict:
    if doc.get("app") != app:
        raise ValueError(f"dossiers.json is for app {doc.get('app')!r}, not {app!r}")
    dossiers = [Dossier.from_json(d) for d in doc["dossiers"] + doc["upgrades"]]
    if not dossiers:
        raise ValueError(f"{app}: no scope has an option; nothing to measure")
    wanted = sorted({d.current for d in dossiers} | {o.item for d in dossiers for o in d.options})
    include = []
    for item in wanted:
        engine_type, name, provider = parse_qualified(item)
        include.append({"provider": provider, "type": engine_type, "name": name})
    return {"schemaVersion": 1, "description": f"call sites of {app} and their replacements", "include": include}
