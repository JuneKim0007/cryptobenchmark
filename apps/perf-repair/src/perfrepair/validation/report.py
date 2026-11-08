"""report.json against its contract: statuses, rows, patterns, recommendations, funnel equal to its recount."""
from __future__ import annotations

from ..dto.report import (COMPILE_STATUSES, DECISION_STATUSES, EDIT_STATUSES, FUNNEL, INTEROP_STATUSES, SCHEMA_VERSION, SOURCES,
                          stayed, unit_counts)
from ..dto.change import CHANGES as CHANGE_CLASSES, REJECT_REASONS, admits
from ..dto.perf_mode import PerfMode
from ..dto.pattern import PATTERN_REASONS, PATTERNS, pattern_of_reason
from .repair import valid_inputs

ROW_KEYS = ("scope", "file", "line", "function", "pattern", "patternReason", "current", "option", "inputs", "decision", "edit",
            "compile", "interop", "deciding", "accepted", "primitive", "unit", "sharedFunction", "stayed")


def _decision(where: str, d: dict) -> list[str]:
    if (d.get("decision") not in DECISION_STATUSES or (d["decision"] != "not_run" and d.get("source") not in SOURCES)):
        return [f"{where}: decision {d}"]
    return []


def _unit(where: str, r: dict) -> list[str]:
    if isinstance(r["unit"], str) and isinstance(r["sharedFunction"], list):
        return []
    return [f"{where}: unit {r['unit']!r} or sharedFunction {r['sharedFunction']!r}"]


def _pattern(where: str, r: dict) -> list[str]:
    if r["patternReason"] not in PATTERN_REASONS or r["pattern"] not in PATTERNS:
        return [f"{where}: pattern {r['pattern']!r} / patternReason {r['patternReason']!r}"]
    return [] if r["pattern"] == pattern_of_reason(r["patternReason"]) else [
        f"{where}: pattern {r['pattern']} is not its reason {r['patternReason']}'s"]


def _row(where: str, r: dict) -> list[str]:
    if tuple(r) != ROW_KEYS:
        return [f"{where}: keys {list(r)}"]
    problems = _decision(where, r["decision"])
    for step, allowed in (("edit", EDIT_STATUSES), ("compile", COMPILE_STATUSES), ("interop", INTEROP_STATUSES)):
        if r[step].get("status") not in allowed:
            problems.append(f"{where}: {step} status {r[step].get('status')!r}")
    if r["inputs"] is not None and not valid_inputs(r["inputs"]):
        problems.append(f"{where}: inputs {r['inputs']}")
    return problems + _unit(where, r) + _pattern(where, r)


def _recount(f: dict, rows: list[dict]) -> dict:
    units = unit_counts(rows)

    def count(step: str, key: str, value: str) -> int:
        return sum(r[step][key] == value for r in rows)
    return {"sites": f["sites"], "scopes": len(rows), "units": units["units"], "withOptions": f["withOptions"],
            "recommend": count("decision", "decision", "recommend"), "replace": count("decision", "decision", "replace"),
            "unitsReplace": units["unitsReplace"], "applied": count("edit", "status", "applied"),
            "compiled": count("compile", "status", "compiled"), "interopPassed": count("interop", "status", "passed")}


def _stayed(rows: list[dict]) -> list[str]:
    stays = stayed(rows)
    return [f"{r['scope']}: stayed {r['stayed']} is not its unit's static keeps beside a replace {stays[r['unit']]}"
            for r in rows if r["stayed"] != stays[r["unit"]]]


def schema_version_problems(doc: dict) -> list[str]:
    return [] if doc.get("schemaVersion") == SCHEMA_VERSION else [f"schemaVersion {doc.get('schemaVersion')!r}"]


def _identity(doc: dict, app: str) -> list[str]:
    problems = schema_version_problems(doc)
    problems += [] if isinstance(doc.get("project"), str) and doc["project"] else [f"project {doc.get('project')!r}"]
    try:
        PerfMode.parse(doc.get("mode"))
    except (ValueError, AttributeError):
        problems.append(f"mode {doc.get('mode')!r} is not a perfMode")
    return problems + ([] if doc.get("app") == app else [f"app {doc.get('app')!r} is not {app!r}"])


def _recommendations(doc: dict) -> list[str]:
    """A recommendation is above maxChange, or it would have been an option; a reject count names a known reason."""
    top = doc.get("maxChange")
    if top not in CHANGE_CLASSES:
        return [f"maxChange {top!r} is not one of {CHANGE_CLASSES}"]
    problems = [f"recommendation {n['scope']} {n['item']}: {n['change']} is not above maxChange {top}"
                for n in doc.get("recommendations") or [] if n["change"] not in CHANGE_CLASSES or admits(top, n["change"])]
    return problems + [f"rejected {k!r} is not a reject reason" for k in doc.get("rejected") or {} if k not in REJECT_REASONS]


def validate_report(doc: dict, app: str) -> list[str]:
    problems = _identity(doc, app)
    rows = doc.get("scopes") or []
    for r in rows:
        problems += _row(str(r.get("scope")), r)
    if problems:
        return problems
    problems += _stayed(rows) + _recommendations(doc)
    f = doc.get("funnel") or {}
    if tuple(f) != FUNNEL or _recount(f, rows) != f or not f["scopes"] >= f["withOptions"] >= f["replace"]:
        problems.append(f"funnel {f} is not the recount of the scope rows")
    return problems
