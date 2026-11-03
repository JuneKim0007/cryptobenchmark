"""Vocabulary of report.json and summary.json: step statuses, reported metrics, funnel stages."""
from __future__ import annotations

from .metrics import METRICS, Metric

# 3: compile not_measurable, interop not_comparable, funnel measuredUnchecked, decision stale; 4: rows carry unit,
# sharedFunction and stayed, funnel units and unitsReplace; 5: metric rows carry selected, the time row its views in the
# display units (report units), summary metrics are the selected ones; 6: maxChange, recommendations, rejected
SCHEMA_VERSION = 6
THROUGHPUT = "throughput"
SOURCES = ("llm", "fallback", "static")
DECISION_STATUSES = ("replace", "keep", "not_run")
EDIT_STATUSES = ("applied", "rejected", "skipped", "not_run")
COMPILE_STATUSES = ("compiled", "primitive_only", "not_measurable", "skipped", "not_run")
INTEROP_STATUSES = ("passed", "unchecked", "not_comparable", "interop_failed", "call_failed", "skipped", "not_run")
MEASURABLE = ("passed", "unchecked")
VERDICTS = ("improves", "not_improving", "not_measured")
# (benchmark.json metric key, unit per operation)
REPORTED = tuple((m.name, m.unit) for m in METRICS)
# measuredUnchecked: of measured, those with no interop check; not a stage
FUNNEL = ("sites", "scopes", "units", "withOptions", "replace", "unitsReplace", "applied", "compiled", "interopPassed", "measured",
          "measuredUnchecked")
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
