"""app.json and scopes.json: shape, contract values, ids recomputed from their parts."""
from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..dto.lifecycle import (BINDINGS, OPEN_ORIGINS, ORIGINS, PARTIAL_REASONS,
                             PARTIALLY_BOUNDED, REQUIREMENTS, ROLES, STATUSES, UNSUPPORTED, UNSUPPORTED_REASONS, WHERE)
from ..dto.site import KEY_SOURCES, SCHEMA_VERSION, SCOPES_SCHEMA_VERSION, SINKS, Scope, scope_id
from ..files import read_json
from .units import validate_units

_SCOPE_TYPES = {"id": str, "app": str, "file": str, "line": int, "call": str, "function": str, "start": int,
                "end": int, "engineType": str, "resolution": str, "sinks": list, "keySource": str}
_LIFECYCLE_KEYS = {"status", "reasons", "binding", "steps", "requirements", "operations"}
_STATUS_REASONS = {UNSUPPORTED: UNSUPPORTED_REASONS, PARTIALLY_BOUNDED: PARTIAL_REASONS}
_OPTIONAL = {"algorithm": str, "provider": str, "keySize": int, "inputSize": int}


def _typed(where: str, d: dict, types: dict, optional: dict) -> list[str]:
    out = [f"{where}: {k} is not {t.__name__}" for k, t in types.items() if not isinstance(d.get(k), t)]
    out += [f"{where}: {k} is not {t.__name__} or null" for k, t in optional.items()
            if d.get(k) is not None and not isinstance(d[k], t)]
    return out


def validate_app_facts(doc: dict) -> list[str]:
    out = [] if doc.get("schemaVersion") == SCHEMA_VERSION else [f"schemaVersion {doc.get('schemaVersion')}"]
    out += _typed(rd.APP, doc, {"app": str, "pathId": str, "root": str, "projectRoot": str, "bundled": list, "registers": list},
                  {"minSdk": int, "targetSdk": int})
    for i, b in enumerate(doc.get("bundled") or []):
        out += _typed(f"bundled[{i}]", b, {"artifact": str}, {"providerName": str})
    for i, r in enumerate(doc.get("registers") or []):
        out += _typed(f"registers[{i}]", r, {"file": str, "line": int, "expr": str}, {})
    return out


def _closed(where: str, rows: list, field: str, values: tuple) -> list[str]:
    return [f"{where}: {field} {r.get(field)!r} is not one of {values}" for r in rows
            if not isinstance(r, dict) or r.get(field) not in values]


def _in_file(n, lines: int | None) -> bool:
    return isinstance(n, int) and n >= 1 and (lines is None or n <= lines)


def _settled_problems(where: str, r: dict, lines: int | None) -> list[str]:
    done, where = r["settled"], f"{where} requirement {r.get('name')}"
    if not isinstance(done, dict) or set(done) != {"origin", "line"}:
        return [f"{where}: settled is not {{origin, line}}"]
    out = [] if done["origin"] in ORIGINS and done["origin"] not in OPEN_ORIGINS else [
        f"{where}: settled origin {done['origin']!r} is not a closed origin"]
    out += [] if _in_file(done["line"], lines) else [f"{where}: settled cites line {done['line']!r}, not a line of the file"]
    return out + ([] if r.get("origin") in OPEN_ORIGINS else [f"{where}: settled over the closed origin {r.get('origin')!r}"])


def _settlements(where: str, lc: dict, lines: int | None) -> list[str]:
    return [p for r in lc["requirements"] if isinstance(r, dict) and r.get("settled") is not None
            for p in _settled_problems(where, r, lines)]


def _lifecycle_values(where: str, lc: dict) -> list[str]:
    out = [] if lc["status"] in STATUSES else [f"{where}: lifecycle status {lc['status']!r} is not one of {STATUSES}"]
    allowed = _STATUS_REASONS.get(lc["status"], ())
    out += [f"{where}: lifecycle reason {r!r} is not one of {allowed} for {lc['status']}" for r in lc["reasons"]
            if r not in allowed]
    if lc["status"] in _STATUS_REASONS and not lc["reasons"]:
        out.append(f"{where}: lifecycle {lc['status']} without a reason")
    if lc["binding"] is not None and lc["binding"] not in BINDINGS:
        out.append(f"{where}: lifecycle binding {lc['binding']!r} is not one of {BINDINGS}")
    out += _closed(f"{where} step", lc["steps"], "role", ROLES) + _closed(f"{where} step", lc["steps"], "where", WHERE)
    out += _closed(f"{where} requirement", lc["requirements"], "name", REQUIREMENTS)
    out += _closed(f"{where} requirement", lc["requirements"], "origin", ORIGINS)
    return out + [f"{where} requirement: depth1 {r.get('depth1')!r} is not a list of {ORIGINS}" for r in lc["requirements"]
                  if isinstance(r, dict) and not set(r.get("depth1") or ()) <= set(ORIGINS)]


def _cited_lines(where: str, lc: dict, lines: int | None) -> list[str]:
    cited = [r.get("line") for r in lc["steps"] if isinstance(r, dict)]
    cited += [r.get(k) for r in lc["requirements"] if isinstance(r, dict) for k in ("line", "at")]
    return [f"{where}: lifecycle cites line {n!r}, not a line of the file" for n in cited
            if not isinstance(n, int) or n < 1 or (lines is not None and n > lines)]


def lifecycle_problems(where: str, lc, lines: int | None = None) -> list[str]:
    """Closed-list values, and with the file's line count, every cited line inside the file."""
    if not isinstance(lc, dict) or not _LIFECYCLE_KEYS <= set(lc):
        return [f"{where}: lifecycle is not a lifecycle object"]
    return _lifecycle_values(where, lc) + _cited_lines(where, lc, lines) + _settlements(where, lc, lines)


def scope_problems(where: str, s, app: str | None, lines: int | None = None) -> list[str]:
    """One scope's shape and contract values; shared by scopes.json and every dossier that carries a scope."""
    if not isinstance(s, dict):
        return [f"{where}: scope is not an object"]
    out = _typed(where, s, _SCOPE_TYPES, _OPTIONAL)
    if s.get("lifecycle") is not None:
        out += lifecycle_problems(where, s["lifecycle"], lines)
    if out:
        return out
    try:
        Scope.from_json(s)
    except (TypeError, KeyError) as e:
        out.append(f"{where}: {e}")
    if s["id"] != scope_id(s["app"], s["file"], s["function"], s["line"], s["call"]):
        out.append(f"{where}: id is not scope_id of its parts")
    if s["app"] != app:
        out.append(f"{where}: app {s['app']!r} is not the document's {app!r}")
    if not s["start"] <= s["line"] <= s["end"]:
        out.append(f"{where}: line {s['line']} outside {s['start']}..{s['end']}")
    if not s["sinks"] or set(s["sinks"]) - set(SINKS):
        out.append(f"{where}: sinks {s['sinks']} not a non-empty subset of {SINKS}")
    if s["keySource"] not in KEY_SOURCES:
        out.append(f"{where}: keySource {s['keySource']} not in {KEY_SOURCES}")
    return out


def validate_scopes(doc: dict, lines: dict[str, int] | None = None) -> list[str]:
    """lines: each source file's line count, when the source is at hand to check cited lines against."""
    out = [] if doc.get("schemaVersion") == SCOPES_SCHEMA_VERSION else [f"schemaVersion {doc.get('schemaVersion')}"]
    out += _typed(rd.SCOPES, doc, {"app": str, "scopes": list, "unscoped": list}, {})
    seen = set()
    for i, s in enumerate(doc.get("scopes") or []):
        out += scope_problems(f"scopes[{i}]", s, doc.get("app"), (lines or {}).get(s.get("file")) if isinstance(s, dict) else None)
        if isinstance(s, dict) and s.get("lifecycle") is None:
            out.append(f"scopes[{i}]: no lifecycle")
        sid = s.get("id") if isinstance(s, dict) else None
        if sid in seen:
            out.append(f"scopes[{i}]: duplicate id {sid}")
        if isinstance(sid, str):
            seen.add(sid)
    return out


def validate_app_dir(directory: Path) -> dict[str, list[str]]:
    out = {}
    for name, check in ((rd.APP, validate_app_facts), (rd.SCOPES, validate_scopes)):
        path = Path(directory) / name
        if path.exists():
            out[f"{Path(directory).name}/{name}"] = check(read_json(path))
    units, scopes = Path(directory) / rd.UNITS, Path(directory) / rd.SCOPES
    if units.exists() and scopes.exists():
        out[f"{Path(directory).name}/{rd.UNITS}"] = validate_units(read_json(units), read_json(scopes)["scopes"])
    return out
