"""app.json and scopes.json: shape, contract values, ids recomputed from their parts."""
from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..dto.site import KEY_SOURCES, SCHEMA_VERSION, SINKS, Scope, scope_id
from ..files import read_json

_SCOPE_TYPES = {"id": str, "app": str, "file": str, "line": int, "call": str, "function": str, "start": int,
                "end": int, "engineType": str, "resolution": str, "sinks": list, "keySource": str}
_OPTIONAL = {"algorithm": str, "provider": str, "keySize": int, "inputSize": int}


def _typed(where: str, d: dict, types: dict, optional: dict) -> list[str]:
    out = [f"{where}: {k} is not {t.__name__}" for k, t in types.items() if not isinstance(d.get(k), t)]
    out += [f"{where}: {k} is not {t.__name__} or null" for k, t in optional.items()
            if d.get(k) is not None and not isinstance(d[k], t)]
    return out


def validate_app_facts(doc: dict) -> list[str]:
    out = [] if doc.get("schemaVersion") == SCHEMA_VERSION else [f"schemaVersion {doc.get('schemaVersion')}"]
    out += _typed(rd.APP, doc, {"app": str, "root": str, "bundled": list, "registers": list},
                  {"minSdk": int, "targetSdk": int})
    for i, b in enumerate(doc.get("bundled") or []):
        out += _typed(f"bundled[{i}]", b, {"artifact": str}, {"providerName": str})
    for i, r in enumerate(doc.get("registers") or []):
        out += _typed(f"registers[{i}]", r, {"file": str, "line": int, "expr": str}, {})
    return out


def validate_scopes(doc: dict) -> list[str]:
    out = [] if doc.get("schemaVersion") == SCHEMA_VERSION else [f"schemaVersion {doc.get('schemaVersion')}"]
    out += _typed(rd.SCOPES, doc, {"app": str, "scopes": list, "unscoped": list}, {})
    seen = set()
    for i, s in enumerate(doc.get("scopes") or []):
        where = f"scopes[{i}]"
        problems = _typed(where, s, _SCOPE_TYPES, _OPTIONAL)
        if problems:
            out += problems
            continue
        try:
            Scope.from_json(s)
        except TypeError as e:
            out.append(f"{where}: {e}")
        if s["id"] != scope_id(s["app"], s["file"], s["function"], s["line"], s["call"]):
            out.append(f"{where}: id is not scope_id of its parts")
        if s["id"] in seen:
            out.append(f"{where}: duplicate id {s['id']}")
        seen.add(s["id"])
        if s["app"] != doc.get("app"):
            out.append(f"{where}: app {s['app']} is not the document's")
        if not s["start"] <= s["line"] <= s["end"]:
            out.append(f"{where}: line {s['line']} outside {s['start']}..{s['end']}")
        if not s["sinks"] or set(s["sinks"]) - set(SINKS):
            out.append(f"{where}: sinks {s['sinks']} not a non-empty subset of {SINKS}")
        if s["keySource"] not in KEY_SOURCES:
            out.append(f"{where}: keySource {s['keySource']} not in {KEY_SOURCES}")
    return out


def validate_app_dir(directory: Path) -> dict[str, list[str]]:
    out = {}
    for name, check in ((rd.APP, validate_app_facts), (rd.SCOPES, validate_scopes)):
        path = Path(directory) / name
        if path.exists():
            out[f"{rd.APPS}/{Path(directory).name}/{name}"] = check(read_json(path))
    return out
