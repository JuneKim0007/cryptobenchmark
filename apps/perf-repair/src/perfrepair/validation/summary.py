"""summary.json against the device's reports: apps and funnels, modes, pattern counts."""
from __future__ import annotations

from ..dto.report import FUNNEL, pattern_counts
from .report import schema_version_problems


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
    return problems
