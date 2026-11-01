"""Vocabulary of report.json and summary.json: step statuses, reported metrics, funnel stages."""
from __future__ import annotations

SCHEMA_VERSION = 1
SOURCES = ("llm", "fallback", "static")
DECISION_STATUSES = ("replace", "keep", "not_run")
EDIT_STATUSES = ("applied", "rejected", "skipped", "not_run")
COMPILE_STATUSES = ("compiled", "primitive_only", "skipped", "not_run")
INTEROP_STATUSES = ("passed", "unchecked", "interop_failed", "call_failed", "skipped", "not_run")
MEASURABLE = ("passed", "unchecked")
VERDICTS = ("improves", "not_improving", "not_measured")
# (benchmark.json metric key, unit per operation)
REPORTED = (("timeNs", "ns/op"), ("allocationCount", "allocations/op"), ("energyJ", "J/op"))
FUNNEL = ("sites", "scopes", "withOptions", "replace", "applied", "compiled", "interopPassed", "measured")
CHANGES = ("improved", "unchanged", "worse", "notMeasured")


def case_id(scope: str, side: str) -> str:
    """cryptobenchmark's scoped case id; side is before or after."""
    return f"scope:{scope}:{side}"
