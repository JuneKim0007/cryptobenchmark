"""report.json against its contract: statuses, rows, patterns, recommendations, funnel equal to its recount."""
from __future__ import annotations

from ..dto.report import (COMPILE_STATUSES, DECISION_STATUSES, EDIT_STATUSES, FUNNEL, INTEROP_STATUSES,
                          MEASURABLE, REPORTED, SCHEMA_VERSION, SOURCES, THERMAL_MISMATCH, THERMAL_THROTTLED, VERDICTS, stayed, unit_counts)
from ..dto.change import CHANGES as CHANGE_CLASSES, REJECT_REASONS, admits
from ..dto.perf_mode import PerfMode
from ..dto.units import DisplayUnits
from ..result.gain import label_of
from ..dto.pattern import PATTERN_REASONS, PATTERNS, pattern_of_reason
from ..result.category import category_mismatch, checkable
from .repair import valid_inputs
from .report_metrics import check_metric, check_selected

ROW_KEYS = ("scope", "file", "line", "function", "pattern", "patternReason", "current", "option", "inputs", "decision", "edit",
            "compile", "interop", "metrics", "verdict", "label", "thermal", "deciding", "accepted", "primitive",
            "categoryMismatch", "truthCheck", "unit", "sharedFunction", "stayed")


def _selection(doc: dict) -> tuple[str, ...] | None:
    try:
        return PerfMode.parse(doc.get("mode")).names
    except (ValueError, AttributeError):
        return None


def _decision(where: str, d: dict) -> list[str]:
    if (d.get("decision") not in DECISION_STATUSES or (d["decision"] != "not_run" and d.get("source") not in SOURCES)
            or not isinstance(d.get("stale"), bool)):
        return [f"{where}: decision {d}"]
    return []


def _unit(where: str, r: dict) -> list[str]:
    if isinstance(r["unit"], str) and isinstance(r["sharedFunction"], list):
        return []
    return [f"{where}: unit {r['unit']!r} or sharedFunction {r['sharedFunction']!r}"]


def _thermal(where: str, t: dict | None) -> list[str]:
    if t is None:
        return []
    return [] if set(t["labels"]) <= {THERMAL_MISMATCH, THERMAL_THROTTLED} else [f"{where}: thermal labels {t['labels']}"]


def _pattern(where: str, r: dict) -> list[str]:
    if r["patternReason"] not in PATTERN_REASONS or r["pattern"] not in PATTERNS:
        return [f"{where}: pattern {r['pattern']!r} / patternReason {r['patternReason']!r}"]
    out = [] if r["pattern"] == pattern_of_reason(r["patternReason"]) else [
        f"{where}: pattern {r['pattern']} is not its reason {r['patternReason']}'s"]
    expected = category_mismatch(r["metrics"], r["primitive"]) if checkable(r) else []
    return out + ([] if r["categoryMismatch"] == expected else [
        f"{where}: categoryMismatch {r['categoryMismatch']} is not the rule's over its metrics and estimates"])


def _row(where: str, r: dict, selected: tuple[str, ...], units: DisplayUnits) -> list[str]:
    if tuple(r) != ROW_KEYS:
        return [f"{where}: keys {list(r)}"]
    problems = _decision(where, r["decision"])
    for step, allowed in (("edit", EDIT_STATUSES), ("compile", COMPILE_STATUSES), ("interop", INTEROP_STATUSES)):
        if r[step].get("status") not in allowed:
            problems.append(f"{where}: {step} status {r[step].get('status')!r}")
    if [m.get("metric") for m in r["metrics"]] != [k for k, _ in REPORTED]:
        problems.append(f"{where}: metrics are not {[k for k, _ in REPORTED]} in order")
    for m in r["metrics"]:
        problems += check_metric(f"{where}.{m.get('metric')}", m, units)
    problems += check_selected(where, r["metrics"], selected)
    if any(m.get("measured") for m in r["metrics"]) and r["interop"].get("status") not in MEASURABLE:
        problems.append(f"{where}: measured although interop is {r['interop'].get('status')}")
    if r["inputs"] is not None and not valid_inputs(r["inputs"]):
        problems.append(f"{where}: inputs {r['inputs']}")
    problems += _unit(where, r)
    if r["verdict"] not in VERDICTS:
        problems.append(f"{where}: verdict {r['verdict']!r}")
    problems += _thermal(where, r["thermal"])
    if r["label"] != label_of([m["change"] for m in r["metrics"] if m.get("measured") and m.get("selected")]):
        problems.append(f"{where}: label {r['label']!r} is not the rule's over its selected metrics")
    return problems


def _status(r: dict) -> tuple:
    return (r["decision"]["decision"], r["edit"]["status"], r["compile"]["status"], r["interop"]["status"],
            any(m["measured"] for m in r["metrics"]))


def _recount(f: dict, rows: list[dict]) -> dict:
    statuses = [_status(r) for r in rows]
    units = unit_counts(rows)

    def count(at: int, value) -> int:
        return sum(s[at] == value for s in statuses)
    return {"sites": f["sites"], "scopes": len(rows), "units": units["units"], "withOptions": f["withOptions"],
            "recommend": count(0, "recommend"), "replace": count(0, "replace"), "unitsReplace": units["unitsReplace"],
            "applied": count(1, "applied"), "compiled": count(2, "compiled"), "interopPassed": count(3, "passed"),
            "measured": count(4, True), "measuredUnchecked": sum(s[4] and s[3] == "unchecked" for s in statuses)}


def _stayed(rows: list[dict]) -> list[str]:
    stays = stayed(rows)
    return [f"{r['scope']}: stayed {r['stayed']} is not its unit's static keeps beside a replace {stays[r['unit']]}"
            for r in rows if r["stayed"] != stays[r["unit"]]]


def _mode_units(doc: dict) -> tuple[tuple[str, ...], DisplayUnits, str | None]:
    """The selection and display units a report was built with, or the problem that stops its check."""
    selected = _selection(doc)
    if selected is None:
        return (), DisplayUnits(), f"mode {doc.get('mode')!r} is not a perfMode"
    try:
        return selected, DisplayUnits.parse(doc["units"]), None
    except (KeyError, ValueError) as e:
        return selected, DisplayUnits(), f"units: {e}"


def _identity(doc: dict, app: str) -> list[str]:
    problems = [] if doc.get("schemaVersion") == SCHEMA_VERSION else [f"schemaVersion {doc.get('schemaVersion')!r}"]
    problems += [] if isinstance(doc.get("project"), str) and doc["project"] else [f"project {doc.get('project')!r}"]
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
    selected, units, stop = _mode_units(doc)
    if stop:
        return problems + [stop]
    rows = doc.get("scopes") or []
    for r in rows:
        problems += _row(str(r.get("scope")), r, selected, units)
    if problems:
        return problems
    # read only over metric rows already found well formed
    problems += [p for r in rows for p in _pattern(str(r["scope"]), r)]
    problems += _stayed(rows) + _recommendations(doc)
    f = doc.get("funnel") or {}
    if tuple(f) != FUNNEL or _recount(f, rows) != f or not f["scopes"] >= f["withOptions"] >= f["replace"]:
        problems.append(f"funnel {f} is not the recount of the scope rows")
    return problems
