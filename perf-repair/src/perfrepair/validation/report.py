"""report.json and summary.json against their contract: statuses, metric rows, funnel equal to its recount."""
from __future__ import annotations

import math

from ..dto.report import (CHANGES, COMPILE_STATUSES, DECISION_STATUSES, EDIT_STATUSES, FUNNEL, INTEROP_STATUSES,
                          MEASURABLE, REPORTED, SCHEMA_VERSION, SOURCES, VERDICTS, stayed, unit_counts)
from ..dto.perf_mode import PerfMode
from ..result.confidence import level
from .repair import valid_inputs

ROW_KEYS = ("scope", "file", "line", "function", "current", "option", "inputs", "decision", "edit", "compile", "interop",
            "metrics", "verdict", "primitive", "unit", "sharedFunction", "stayed")
MEASURED_KEYS = {"metric", "unit", "selected", "measured", "before", "after", "ratio", "pImprove", "level", "n"}


def _selection(doc: dict) -> tuple[str, ...] | None:
    try:
        return PerfMode.parse(doc.get("mode")).names
    except (ValueError, AttributeError):
        return None


def _metric(where: str, m: dict, selected: tuple[str, ...]) -> list[str]:
    if m.get("selected") is not (m.get("metric") in selected):
        return [f"{where}: selected {m.get('selected')!r} is not whether the mode selects it"]
    if m.get("measured") is False:
        ok = set(m) == {"metric", "unit", "selected", "measured", "reason"} and isinstance(m["reason"], str) and m["reason"]
        return [] if ok else [f"{where}: an unmeasured metric has exactly a non-empty reason and no numbers"]
    extra = {"throughput"} if m.get("metric") == "timeNs" else set(m) & {"kind"}
    if set(m) != MEASURED_KEYS | extra:
        return [f"{where}: keys {sorted(m)}"]
    problems = []
    if not all(isinstance(m[k], (int, float)) and math.isfinite(m[k]) and m[k] >= 0 for k in ("before", "after")):
        problems.append(f"{where}: before and after must be finite and not negative")
    elif m["ratio"] != (m["after"] / m["before"] if m["before"] else None):
        problems.append(f"{where}: ratio {m['ratio']} is not after ÷ before")
    if m["level"] != level(m["pImprove"]):
        problems.append(f"{where}: level {m['level']} is not the grade of pImprove {m['pImprove']}")
    return problems


def _decision(where: str, d: dict) -> list[str]:
    if (d.get("decision") not in DECISION_STATUSES or (d["decision"] != "not_run" and d.get("source") not in SOURCES)
            or not isinstance(d.get("stale"), bool)):
        return [f"{where}: decision {d}"]
    return []


def _unit(where: str, r: dict) -> list[str]:
    if isinstance(r["unit"], str) and isinstance(r["sharedFunction"], list):
        return []
    return [f"{where}: unit {r['unit']!r} or sharedFunction {r['sharedFunction']!r}"]


def _row(where: str, r: dict, selected: tuple[str, ...]) -> list[str]:
    if tuple(r) != ROW_KEYS:
        return [f"{where}: keys {list(r)}"]
    problems = _decision(where, r["decision"])
    for step, allowed in (("edit", EDIT_STATUSES), ("compile", COMPILE_STATUSES), ("interop", INTEROP_STATUSES)):
        if r[step].get("status") not in allowed:
            problems.append(f"{where}: {step} status {r[step].get('status')!r}")
    if [m.get("metric") for m in r["metrics"]] != [k for k, _ in REPORTED]:
        problems.append(f"{where}: metrics are not {[k for k, _ in REPORTED]} in order")
    for m in r["metrics"]:
        problems += _metric(f"{where}.{m.get('metric')}", m, selected)
    if any(m.get("measured") for m in r["metrics"]) and r["interop"].get("status") not in MEASURABLE:
        problems.append(f"{where}: measured although interop is {r['interop'].get('status')}")
    if r["inputs"] is not None and not valid_inputs(r["inputs"]):
        problems.append(f"{where}: inputs {r['inputs']}")
    problems += _unit(where, r)
    if r["verdict"] not in VERDICTS:
        problems.append(f"{where}: verdict {r['verdict']!r}")
    return problems


def _recount(f: dict, rows: list[dict]) -> dict:
    statuses = [(r["decision"]["decision"], r["edit"]["status"], r["compile"]["status"], r["interop"]["status"],
                 any(m["measured"] for m in r["metrics"])) for r in rows]
    units = unit_counts(rows)
    return {"sites": f["sites"], "scopes": len(rows), "units": units["units"], "withOptions": f["withOptions"],
            "replace": sum(s[0] == "replace" for s in statuses), "unitsReplace": units["unitsReplace"], "applied": sum(s[1] == "applied" for s in statuses),
            "compiled": sum(s[2] == "compiled" for s in statuses),
            "interopPassed": sum(s[3] == "passed" for s in statuses), "measured": sum(s[4] for s in statuses),
            "measuredUnchecked": sum(s[4] and s[3] == "unchecked" for s in statuses)}


def _stayed(rows: list[dict]) -> list[str]:
    stays = stayed(rows)
    return [f"{r['scope']}: stayed {r['stayed']} is not its unit's static keeps beside a replace {stays[r['unit']]}"
            for r in rows if r["stayed"] != stays[r["unit"]]]


def validate_report(doc: dict, app: str) -> list[str]:
    problems = [] if doc.get("schemaVersion") == SCHEMA_VERSION else [f"schemaVersion {doc.get('schemaVersion')!r}"]
    if doc.get("app") != app:
        problems.append(f"app {doc.get('app')!r} is not {app!r}")
    if (selected := _selection(doc)) is None:
        return problems + [f"mode {doc.get('mode')!r} is not a perfMode"]
    rows = doc.get("scopes") or []
    for r in rows:
        problems += _row(str(r.get("scope")), r, selected)
    if problems:
        return problems
    problems += _stayed(rows)
    f = doc.get("funnel") or {}
    if tuple(f) != FUNNEL or _recount(f, rows) != f or not f["scopes"] >= f["withOptions"] >= f["replace"]:
        problems.append(f"funnel {f} is not the recount of the scope rows")
    return problems


def validate_summary(doc: dict, reports: list[dict]) -> list[str]:
    """`reports`: the device's <app>/report.json documents."""
    problems = [] if doc.get("schemaVersion") == SCHEMA_VERSION else [f"schemaVersion {doc.get('schemaVersion')!r}"]
    by_app = {r["app"]: r["funnel"] for r in reports}
    if doc.get("apps") != sorted(by_app) or doc.get("byApp") != by_app:
        problems.append(f"apps {doc.get('apps')} and byApp are not the reports' apps and funnels")
    if doc.get("funnel") != {k: sum(f[k] for f in by_app.values()) for k in FUNNEL}:
        problems.append("funnel is not the sum of byApp")
    selected = _selection(doc)
    if selected is None or list(doc.get("metrics") or {}) != list(selected):
        problems.append(f"metrics {list(doc.get('metrics') or {})} are not the mode's selected metrics {selected}")
    for metric, m in (doc.get("metrics") or {}).items():
        if sorted(a for c in CHANGES for a in m["apps"][c]) != sorted(by_app):
            problems.append(f"{metric}: the change classes do not partition the apps")
        if sorted(a for a, v in m["ratios"].items() if v is None) != m["apps"]["notMeasured"]:
            problems.append(f"{metric}: notMeasured is not the apps without a ratio")
    return problems
