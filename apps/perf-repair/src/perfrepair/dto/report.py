"""Vocabulary of report.json and summary.json: step statuses, reported metrics, funnel stages."""
from __future__ import annotations

from .metrics import METRICS, Metric
from .pattern import PATTERNS, UNKNOWN_DEFAULT

# 3: compile not_measurable, interop not_comparable, funnel measuredUnchecked, decision stale; 4: rows carry unit,
# sharedFunction and stayed, funnel units and unitsReplace; 5: metric rows carry selected, the time row its views in the
# display units (report units), summary metrics are the selected ones; 6: maxChange, recommendations, rejected
# 7: rows carry label and thermal, measured metric rows change and noise; a report names its project and source; summary modes, labels, swaps, thermal
# 8: rows carry pattern, patternReason, categoryMismatch; summary metrics, labels and swaps per pattern, never mixed
# 9: rows carry measuredBy and measurements, each kind's numbers and truth check; funnel measuredCallSite, after measured
# 10: brokenUses, each broken use and what it became; summary brokenUses
SCHEMA_VERSION = 10
BROKEN_USES = "brokenUses"
FUNCTION, CALL_SITE = "function", "callSite"
THERMAL_MISMATCH, THERMAL_THROTTLED = "thermal_mismatch", "thermal_throttled_at_end"
THROUGHPUT = "throughput"
SOURCES = ("llm", "fallback", "static", "list")
DECISION_STATUSES = ("replace", "keep", "recommend", "not_run")
EDIT_STATUSES = ("applied", "rejected", "skipped", "not_run")
COMPILE_STATUSES = ("compiled", "primitive_only", "not_measurable", "skipped", "not_run")
INTEROP_STATUSES = ("passed", "unchecked", "not_comparable", "interop_failed", "call_failed", "skipped", "not_run")
MEASURABLE = ("passed", "unchecked")
VERDICTS = ("improves", "not_improving", "not_measured")
# (benchmark.json metric key, unit per operation)
REPORTED = tuple((m.name, m.unit) for m in METRICS)
# measured: the function itself; measuredCallSite: only the swapped call alone; measuredUnchecked: of measured, those with no interop check; not stages
FUNNEL = ("sites", "scopes", "units", "withOptions", "recommend", "replace", "unitsReplace", "applied", "compiled", "interopPassed", "measured",
          "measuredCallSite", "measuredUnchecked")
CHANGES = ("improved", "unchanged", "worse", "notMeasured")


def has_views(metric: Metric) -> bool:
    """A metric throughput selects is time: its row carries latency and throughput in the display units."""
    return THROUGHPUT in metric.selects


def unit_counts(rows: list[dict]) -> dict:
    return {"units": len({r["unit"] for r in rows}),
            "unitsReplace": len({r["unit"] for r in rows if r["decision"]["decision"] == "replace"})}


def stayed(rows: list[dict]) -> dict[str, list[str]]:
    """Per unit, its members a static keep left on what they use while another member is replaced."""
    replaced = {r["unit"] for r in rows if r["decision"]["decision"] == "replace"}
    out: dict[str, list[str]] = {r["unit"]: [] for r in rows}
    for r in rows:
        if r["unit"] in replaced and r["decision"]["source"] == "static":
            out[r["unit"]].append(r["scope"])
    return out


def case_id(scope: str, side: str) -> str:
    """cryptobenchmark's scoped case id; side is before or after."""
    return f"scope:{scope}:{side}"


def call_site_case_id(scope: str, side: str) -> str:
    return f"scope:{scope}:callSite:{side}"


def of_pattern(reports: list[dict], pattern: str) -> list[dict]:
    """Each report with only the rows of one category, so no count or ratio mixes the two."""
    return [{**r, "scopes": [s for s in r["scopes"] if s["pattern"] == pattern]} for r in reports]


def pattern_counts(reports: list[dict]) -> dict:
    def counts(rows: list[dict]) -> dict:
        return {**{p: sum(s["pattern"] == p for s in rows) for p in PATTERNS},
                "unknownDefault": sum(s["patternReason"] == UNKNOWN_DEFAULT for s in rows),
                "categoryMismatch": sum(bool(s["categoryMismatch"]) for s in rows)}
    return {"all": counts([s for r in reports for s in r["scopes"]]), "byApp": {r["app"]: counts(r["scopes"]) for r in reports}}
