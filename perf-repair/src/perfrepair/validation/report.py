"""report.json and summary.json against their contract: statuses, metric rows, funnel equal to its recount."""
from __future__ import annotations

import math

from ..dto.report import (CHANGES, COMPILE_STATUSES, DECISION_STATUSES, EDIT_STATUSES, FUNNEL, INTEROP_STATUSES,
                          MEASURABLE, REPORTED, SCHEMA_VERSION, SOURCES, THERMAL_MISMATCH, THERMAL_THROTTLED, VERDICTS, stayed, unit_counts)
from ..dto.change import CHANGES as CHANGE_CLASSES, REJECT_REASONS, admits
from ..dto.metrics import BY_NAME, NAMES
from ..dto.perf_mode import PerfMode
from ..dto.report import has_views
from ..dto.units import DisplayUnits
from ..result.confidence import level
from ..result.gain import change_of, label_of, noise_of
from .repair import valid_inputs

ROW_KEYS = ("scope", "file", "line", "function", "current", "option", "inputs", "decision", "edit", "compile", "interop",
            "metrics", "verdict", "label", "thermal", "deciding", "accepted", "primitive", "unit", "sharedFunction", "stayed")
MEASURED_KEYS = {"metric", "unit", "selected", "measured", "before", "after", "ratio", "pImprove", "level", "n", "noise", "change"}


def _selection(doc: dict) -> tuple[str, ...] | None:
    try:
        return PerfMode.parse(doc.get("mode")).names
    except (ValueError, AttributeError):
        return None


def _views(where: str, m: dict, units: DisplayUnits) -> list[str]:
    """The time row's display: latency is its medians in the latency unit, throughput their inverse in its unit or null."""
    v = m.get("views")
    if "views" not in m:
        return []
    if v is None:
        return [] if not (m["before"] > 0 and m["after"] > 0) else [f"{where}: views null for positive medians"]
    lat, tput = v.get("latency") or {}, v.get("throughput")
    if lat != {"unit": units.latency_label, "before": units.latency_of(m["before"]), "after": units.latency_of(m["after"])}:
        return [f"{where}: latency view {lat} is not the medians in {units.latency_label}"]
    if tput is not None and (tput.get("unit") != units.throughput
                             or not math.isclose(tput["before"] * m["before"], tput["after"] * m["after"], rel_tol=1e-9)):
        return [f"{where}: throughput view {tput} is not the medians' inverse in {units.throughput}"]
    return []


def _extra(m: dict) -> set[str]:
    """The keys a measured row adds: views on the time metric, else kind when energy was estimated."""
    metric = BY_NAME.get(m.get("metric"))
    return {"views"} if metric and has_views(metric) else set(m) & {"kind"}


def _selected(where: str, metrics: list[dict], selected: tuple[str, ...]) -> list[str]:
    return [f"{where}.{m.get('metric')}: selected {m.get('selected')!r} is not whether the mode selects it"
            for m in metrics if m.get("selected") is not (m.get("metric") in selected)]


def _metric(where: str, m: dict, units: DisplayUnits) -> list[str]:
    if m.get("measured") is False:
        ok = set(m) == {"metric", "unit", "selected", "measured", "reason"} and isinstance(m["reason"], str) and m["reason"]
        return [] if ok else [f"{where}: an unmeasured metric has exactly a non-empty reason and no numbers"]
    if set(m) != MEASURED_KEYS | _extra(m):
        return [f"{where}: keys {sorted(m)}"]
    problems = []
    if not all(isinstance(m[k], (int, float)) and math.isfinite(m[k]) and m[k] >= 0 for k in ("before", "after")):
        problems.append(f"{where}: before and after must be finite and not negative")
    elif m["ratio"] != (m["after"] / m["before"] if m["before"] else None):
        problems.append(f"{where}: ratio {m['ratio']} is not after ÷ before")
    if m["level"] != level(m["pImprove"]):
        problems.append(f"{where}: level {m['level']} is not the grade of pImprove {m['pImprove']}")
    if m["noise"] != noise_of(m["pImprove"]) or m["change"] != change_of(m["ratio"], m["pImprove"]):
        problems.append(f"{where}: noise {m['noise']} or change {m['change']} is not the rule's for its ratio and pImprove")
    return problems or _views(where, m, units)


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
        problems += _metric(f"{where}.{m.get('metric')}", m, units)
    problems += _selected(where, r["metrics"], selected)
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
    problems += _stayed(rows) + _recommendations(doc)
    f = doc.get("funnel") or {}
    if tuple(f) != FUNNEL or _recount(f, rows) != f or not f["scopes"] >= f["withOptions"] >= f["replace"]:
        problems.append(f"funnel {f} is not the recount of the scope rows")
    return problems


def _union(reports: list[dict]) -> list[str]:
    chosen = {n for r in reports for n in PerfMode.parse(r["mode"]).names}
    return [n for n in NAMES if n in chosen]


def validate_summary(doc: dict, reports: list[dict]) -> list[str]:
    """`reports`: the device's <app>/report.json documents."""
    problems = [] if doc.get("schemaVersion") == SCHEMA_VERSION else [f"schemaVersion {doc.get('schemaVersion')!r}"]
    by_app = {r["app"]: r["funnel"] for r in reports}
    if doc.get("apps") != sorted(by_app) or doc.get("byApp") != by_app:
        problems.append(f"apps {doc.get('apps')} and byApp are not the reports' apps and funnels")
    if doc.get("funnel") != {k: sum(f[k] for f in by_app.values()) for k in FUNNEL}:
        problems.append("funnel is not the sum of byApp")
    selected = _union(reports)
    if list(doc.get("metrics") or {}) != list(selected):
        problems.append(f"metrics {list(doc.get('metrics') or {})} are not the apps' selected metrics {selected}")
    if doc.get("modes") != {r["app"]: r["mode"] for r in reports}:
        problems.append("modes are not each report's own")
    for metric, m in (doc.get("metrics") or {}).items():
        if sorted(a for c in CHANGES for a in m["apps"][c]) != sorted(by_app):
            problems.append(f"{metric}: the change classes do not partition the apps")
        if sorted(a for a, v in m["ratios"].items() if v is None) != m["apps"]["notMeasured"]:
            problems.append(f"{metric}: notMeasured is not the apps without a ratio")
    return problems
