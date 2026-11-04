"""dossiers.json as a document: its header and perfMode, noOptions codes, notOffered candidates."""
from __future__ import annotations

from ...dto.change import CHANGES, CLASSES, REJECT_REASONS, REJECTED, admits
from ...dto.dossier import NO_OPTION_REASONS, reason_code
from ...dto.perf_mode import PerfMode
from ...dto.site import DOSSIERS_SCHEMA_VERSION

KEYS = {"schemaVersion", "app", "perfMode", "maxChange", "dossiers", "noOptions", "notOffered", "units"}
NOT_OFFERED_KEYS = {"scope", "item", "change", "diff", "reasons", "outputChanges"}


def check_header(doc) -> list[str]:
    if not isinstance(doc, dict):
        return ["dossiers.json is not an object"]
    problems = [] if set(doc) == KEYS else [f"keys {sorted(doc)} are not {sorted(KEYS)}"]
    if doc.get("schemaVersion") != DOSSIERS_SCHEMA_VERSION:
        problems.append(f"schemaVersion {doc.get('schemaVersion')} is not {DOSSIERS_SCHEMA_VERSION}")
    problems += [f"{k} is not a list" for k in ("dossiers", "noOptions", "notOffered", "units")
                 if not isinstance(doc.get(k), list)]
    if doc.get("maxChange") not in CHANGES:
        problems.append(f"maxChange {doc.get('maxChange')!r} is not one of {CHANGES}")
    if perf_of(doc) is None:
        problems.append(f"perfMode {doc.get('perfMode')!r} does not parse")
    return problems + ([] if isinstance(doc.get("app"), str) else ["app is not a string"])


def perf_of(doc: dict) -> PerfMode | None:
    try:
        return PerfMode.parse(doc.get("perfMode"))
    except (ValueError, AttributeError):
        return None


def check_no_options(doc: dict) -> list[str]:
    problems = []
    for i, n in enumerate(doc.get("noOptions") or []):
        if not isinstance(n, dict) or set(n) != {"scope", "reason"} or not isinstance(n["scope"], str):
            problems.append(f"noOptions[{i}]: is not a {{scope, reason}} object")
        elif not isinstance(n["reason"], str) or reason_code(n["reason"]) not in NO_OPTION_REASONS:
            problems.append(f"noOptions {n['scope']}: reason {n['reason']!r} is not one of {NO_OPTION_REASONS}")
    return problems


def check_not_offered(doc: dict) -> list[str]:
    """A candidate not offered is rejected with reasons, or of a class above maxChange: a recommendation."""
    problems, top = [], doc.get("maxChange")
    for i, n in enumerate(doc.get("notOffered") or []):
        where = f"notOffered[{i}]"
        if not isinstance(n, dict) or set(n) != NOT_OFFERED_KEYS:
            problems.append(f"{where}: keys are not {sorted(NOT_OFFERED_KEYS)}")
        elif n["change"] not in CLASSES:
            problems.append(f"{where}: change {n['change']!r} is not one of {CLASSES}")
        elif (n["change"] == REJECTED) != bool(n["reasons"]) or not set(n["reasons"]) <= set(REJECT_REASONS):
            problems.append(f"{where}: reasons {n['reasons']!r} are not reject reasons of a rejected candidate")
        elif top in CHANGES and admits(top, n["change"]):
            problems.append(f"{where}: {n['change']} is within maxChange {top}; it is an option")
    return problems
