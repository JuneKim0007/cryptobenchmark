"""bundled-suggestions.yaml: counts agree with the lists, a matched row carries its entry at the pinned version, a blocked
or unmatched one a reason and no entry, and only apply applies."""
from __future__ import annotations

from ..dto.bundled import APPLY, FROM_APPS, OFF, SCHEMA_VERSION, UNMATCHED_REASONS

KINDS = ("matched", "blocked", "unmatched")


def _common(where: str, s: dict) -> list[str]:
    apps = s.get("apps")
    out = [] if isinstance(s.get("provider"), str) and s["provider"] else [f"{where}: no provider"]
    if not (isinstance(apps, list) and apps and all(isinstance(a, str) for a in apps)):
        out.append(f"{where}: apps is not a non-empty list of app ids")
    return out


def _matched(where: str, s: dict, from_apps: str) -> list[str]:
    entry = s.get("entry")
    if not isinstance(entry, dict) or not isinstance(entry.get("create"), str):
        return [f"{where}: no entry with create"]
    out = [] if entry.get("artifact") == f"{s.get('artifact')}:{s.get('version')}" else [
        f"{where}: entry artifact {entry.get('artifact')!r} is not {s.get('artifact')}:{s.get('version')}"]
    if s.get("reason"):
        out.append(f"{where}: a matched row has a reason")
    if s.get("applied") and from_apps != APPLY:
        out.append(f"{where}: applied with fromApps {from_apps}")
    return out


def _not_used(where: str, s: dict, kind: str) -> list[str]:
    reason = s.get("reason")
    out = [f"{where}: {k} on a {kind} row" for k in ("entry", "applied") if s.get(k)]
    if not (isinstance(reason, str) and reason.strip()):
        out.append(f"{where}: no reason")
    elif kind == "unmatched" and reason not in UNMATCHED_REASONS:
        out.append(f"{where}: reason {reason!r} is not one of {list(UNMATCHED_REASONS)}")
    return out


def _row(kind: str, where: str, s, from_apps) -> list[str]:
    if not isinstance(s, dict):
        return [f"{where}: not a mapping"]
    return _common(where, s) + (_matched(where, s, from_apps) if kind == "matched" else _not_used(where, s, kind))


def _counts(doc: dict, lists: dict) -> list[str]:
    counts = doc.get("counts") or {}
    applied = sum(1 for s in lists["matched"] if isinstance(s, dict) and s.get("applied"))
    expected = {**{k: len(v) for k, v in lists.items()}, "applied": applied}
    return [f"counts.{k} {counts.get(k)}, the file lists {n}" for k, n in expected.items() if counts.get(k) != n]


def validate_suggestions(doc: dict) -> list[str]:
    if not isinstance(doc, dict) or doc.get("schemaVersion") != SCHEMA_VERSION:
        return [f"schemaVersion is not {SCHEMA_VERSION}"]
    from_apps = doc.get("fromApps")
    out = [] if from_apps in FROM_APPS and from_apps != OFF else [f"fromApps {from_apps!r} writes no suggestions"]
    lists = {k: doc.get(k) if isinstance(doc.get(k), list) else [] for k in (*KINDS, "missing")}
    out += [p for kind in KINDS for i, s in enumerate(lists[kind]) for p in _row(kind, f"{kind}[{i}]", s, from_apps)]
    return out + _counts(doc, lists)
