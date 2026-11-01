"""report.json and summary.json against their contract: statuses, metric rows, funnel equal to its recount."""
from __future__ import annotations

import math

from ..dto.report import (CHANGES, COMPILE_STATUSES, DECISION_STATUSES, EDIT_STATUSES, FUNNEL, INTEROP_STATUSES,
                          MEASURABLE, REPORTED, SCHEMA_VERSION, SOURCES, VERDICTS)
from ..result.confidence import level

ROW_KEYS = ("scope", "file", "line", "function", "current", "option", "decision", "edit", "compile", "interop",
            "metrics", "verdict", "primitive")
MEASURED_KEYS = {"metric", "unit", "measured", "before", "after", "ratio", "pImprove", "level", "n"}


def _metric(where: str, m: dict) -> list[str]:
    if m.get("measured") is False:
        ok = set(m) == {"metric", "unit", "measured", "reason"} and isinstance(m["reason"], str) and m["reason"]
        return [] if ok else [f"{where}: an unmeasured metric has exactly a non-empty reason and no numbers"]
    extra = {"throughput"} if m.get("metric") == "timeNs" else set()
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


def _row(where: str, r: dict) -> list[str]:
    if tuple(r) != ROW_KEYS:
        return [f"{where}: keys {list(r)}"]
    d, problems = r["decision"], []
    if d.get("decision") not in DECISION_STATUSES or (d["decision"] != "not_run" and d.get("source") not in SOURCES):
        problems.append(f"{where}: decision {d}")
    for step, allowed in (("edit", EDIT_STATUSES), ("compile", COMPILE_STATUSES), ("interop", INTEROP_STATUSES)):
        if r[step].get("status") not in allowed:
            problems.append(f"{where}: {step} status {r[step].get('status')!r}")
    if [m.get("metric") for m in r["metrics"]] != [k for k, _ in REPORTED]:
        problems.append(f"{where}: metrics are not {[k for k, _ in REPORTED]} in order")
    for m in r["metrics"]:
        problems += _metric(f"{where}.{m.get('metric')}", m)
    if any(m.get("measured") for m in r["metrics"]) and r["interop"].get("status") not in MEASURABLE:
        problems.append(f"{where}: measured although interop is {r['interop'].get('status')}")
    if r["verdict"] not in VERDICTS:
        problems.append(f"{where}: verdict {r['verdict']!r}")
    return problems


def _recount(f: dict, rows: list[dict]) -> dict:
    statuses = [(r["decision"]["decision"], r["edit"]["status"], r["compile"]["status"], r["interop"]["status"],
                 any(m["measured"] for m in r["metrics"])) for r in rows]
    return {"sites": f["sites"], "scopes": len(rows), "withOptions": f["withOptions"],
            "replace": sum(s[0] == "replace" for s in statuses), "applied": sum(s[1] == "applied" for s in statuses),
            "compiled": sum(s[2] == "compiled" for s in statuses),
            "interopPassed": sum(s[3] == "passed" for s in statuses), "measured": sum(s[4] for s in statuses)}


def validate_report(doc: dict, app: str) -> list[str]:
    problems = [] if doc.get("schemaVersion") == SCHEMA_VERSION else [f"schemaVersion {doc.get('schemaVersion')!r}"]
    if doc.get("app") != app:
        problems.append(f"app {doc.get('app')!r} is not {app!r}")
    rows = doc.get("scopes") or []
    for r in rows:
        problems += _row(str(r.get("scope")), r)
    if problems:
        return problems
    f = doc.get("funnel") or {}
    if tuple(f) != FUNNEL or _recount(f, rows) != f or not f["scopes"] >= f["withOptions"] >= f["replace"]:
        problems.append(f"funnel {f} is not the recount of the scope rows")
    return problems


def validate_summary(doc: dict, reports: list[dict]) -> list[str]:
    """`reports`: the run's apps/<app>/report.json documents."""
    problems = [] if doc.get("schemaVersion") == SCHEMA_VERSION else [f"schemaVersion {doc.get('schemaVersion')!r}"]
    by_app = {r["app"]: r["funnel"] for r in reports}
    if doc.get("apps") != sorted(by_app) or doc.get("byApp") != by_app:
        problems.append(f"apps {doc.get('apps')} and byApp are not the reports' apps and funnels")
    if doc.get("funnel") != {k: sum(f[k] for f in by_app.values()) for k in FUNNEL}:
        problems.append("funnel is not the sum of byApp")
    if list(doc.get("metrics") or {}) != [k for k, _ in REPORTED]:
        problems.append(f"metrics are not {[k for k, _ in REPORTED]}")
    for metric, m in (doc.get("metrics") or {}).items():
        if sorted(a for c in CHANGES for a in m["apps"][c]) != sorted(by_app):
            problems.append(f"{metric}: the change classes do not partition the apps")
        if sorted(a for a, v in m["ratios"].items() if v is None) != m["apps"]["notMeasured"]:
            problems.append(f"{metric}: notMeasured is not the apps without a ratio")
    return problems
