"""summary.json against the device's reports: apps and funnels, modes, pattern counts, one metrics block per pattern."""
from __future__ import annotations

from ..dto.metrics import NAMES
from ..dto.pattern import PATTERNS
from ..dto.perf_mode import PerfMode
from ..dto.report import CHANGES, FUNNEL, pattern_counts
from .report import schema_version_problems


def _union(reports: list[dict]) -> list[str]:
    chosen = {n for r in reports for n in PerfMode.parse(r["mode"]).names}
    return [n for n in NAMES if n in chosen]


def validate_summary(doc: dict, reports: list[dict]) -> list[str]:
    """`reports`: the device's <app>/report.json documents."""
    problems = schema_version_problems(doc)
    by_app = {r["app"]: r["funnel"] for r in reports}
    if doc.get("apps") != sorted(by_app) or doc.get("byApp") != by_app:
        problems.append(f"apps {doc.get('apps')} and byApp are not the reports' apps and funnels")
    if doc.get("funnel") != {k: sum(f[k] for f in by_app.values()) for k in FUNNEL}:
        problems.append("funnel is not the sum of byApp")
    if doc.get("modes") != {r["app"]: r["mode"] for r in reports}:
        problems.append("modes are not each report's own")
    if doc.get("patterns") != pattern_counts(reports):
        problems.append("patterns are not the count of the reports' rows per pattern")
    by_pattern = doc.get("metrics") or {}
    if list(by_pattern) != list(PATTERNS) or list(doc.get("labels") or {}) != list(PATTERNS):
        return problems + [f"metrics and labels are not one block per pattern {PATTERNS}"]
    for pattern, metrics in by_pattern.items():
        problems += _summary_metrics(pattern, metrics, _union(reports), sorted(by_app))
    return problems + [f"swap {s.get('current')} → {s.get('option')}: pattern {s.get('pattern')!r}"
                       for s in doc.get("swaps") or [] if s.get("pattern") not in PATTERNS]


def _summary_metrics(pattern: str, metrics: dict, selected: list[str], apps: list[str]) -> list[str]:
    if list(metrics) != list(selected):
        return [f"{pattern} metrics {list(metrics)} are not the apps' selected metrics {selected}"]
    problems = []
    for metric, m in metrics.items():
        if sorted(a for c in CHANGES for a in m["apps"][c]) != apps:
            problems.append(f"{pattern} {metric}: the change classes do not partition the apps")
        if sorted(a for a, v in m["ratios"].items() if v is None) != m["apps"]["notMeasured"]:
            problems.append(f"{pattern} {metric}: notMeasured is not the apps without a ratio")
    return problems
