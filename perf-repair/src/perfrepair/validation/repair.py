"""edits.json and harness.yaml checked against their contract and against each other."""
from __future__ import annotations

from pathlib import Path

from ..dto.site import METRICS, SCHEMA_VERSION
from ..source.language import NAMES

EDIT_REASONS = ("call_moved", "ambiguous_call", "function_span", "unbalanced_call", "unsupported_expression",
                "algorithm_not_literal", "no_init", "ambiguous_init", "missing_parameter",
                "unknown_parameters", "unsupported_kind", "unsupported_language", "file_missing", "no_edits",
                "no_change", "overlapping_edits")
HARNESS_KEYS = ("id", "language", "function", "before", "after", "imports", "inputs", "current", "option",
                "metrics", "dependencies")


def _header(doc: dict, app: str, key: str) -> list[str]:
    problems = []
    if doc.get("schemaVersion") != SCHEMA_VERSION:
        problems.append(f"schemaVersion is {doc.get('schemaVersion')!r}")
    if doc.get("app") != app:
        problems.append(f"app is {doc.get('app')!r}, not {app!r}")
    if not isinstance(doc.get(key), list):
        problems.append(f"{key} is not a list")
    return problems


def validate_edits(doc: dict, app: str, scope_ids: set[str]) -> list[str]:
    problems = _header(doc, app, "edits")
    seen = set()
    for e in doc.get("edits") or []:
        where = e.get("scope")
        if where not in scope_ids:
            problems.append(f"{where}: not a scope of {app}")
        if where in seen:
            problems.append(f"{where}: listed twice")
        seen.add(where)
        if e.get("status") == "applied":
            if e.get("reason") is not None or not e.get("diff"):
                problems.append(f"{where}: applied needs a diff and no reason")
        elif e.get("status") == "rejected":
            if e.get("reason") not in EDIT_REASONS or e.get("diff") != "":
                problems.append(f"{where}: rejected needs a coded reason and an empty diff")
        else:
            problems.append(f"{where}: status {e.get('status')!r}")
    return problems


def _size(value) -> bool:
    return value is None or (type(value) is int and value > 0)


def validate_harness(doc: dict, app: str, base: Path, edits: dict) -> list[str]:
    """`base` is harness.yaml's folder; the scopes are exactly the applied edits."""
    problems = _header(doc, app, "scopes")
    applied = sorted(e["scope"] for e in edits.get("edits") or [] if e.get("status") == "applied")
    scopes = doc.get("scopes") or []
    if [s.get("id") for s in scopes] != applied:
        problems.append("scopes are not exactly the applied edits, in id order")
    for s in scopes:
        where = s.get("id")
        if tuple(s) != HARNESS_KEYS:
            problems.append(f"{where}: keys {list(s)}")
            continue
        if s["language"] not in NAMES:
            problems.append(f"{where}: language {s['language']!r}")
        paths = [base / s[side] for side in ("before", "after")]
        if not all(p.is_file() for p in paths):
            problems.append(f"{where}: before or after file missing")
        elif paths[0].read_bytes() == paths[1].read_bytes():
            problems.append(f"{where}: before and after are the same")
        if not all(isinstance(i, str) and i.startswith("import ") for i in s["imports"]):
            problems.append(f"{where}: an import is not an import line")
        if set(s["inputs"]) != {"inputSize", "keySize"} or not all(map(_size, s["inputs"].values())):
            problems.append(f"{where}: inputs {s['inputs']}")
        if not isinstance(s["option"], str) or not isinstance(s["current"], str) or s["current"] == s["option"]:
            problems.append(f"{where}: current {s['current']!r} and option {s['option']!r} are not two items")
        if s["metrics"] != list(METRICS):
            problems.append(f"{where}: metrics {s['metrics']}")
        if s["dependencies"] != sorted(set(s["dependencies"])):
            problems.append(f"{where}: dependencies are not sorted and unique")
    return problems
