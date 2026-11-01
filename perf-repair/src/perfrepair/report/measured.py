"""cryptobenchmark's --harness output for one app: each scope's scoped-plan record and its measured cases."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..files import read_json, read_yaml
from ..run_dir import AppPaths


@dataclass(frozen=True)
class Measured:
    """`absent` says why there is no plan; `cases` is keyed by case id and empty when nothing was measured."""
    absent: str | None
    plan: dict[str, dict] = field(default_factory=dict)
    cases: dict[str, dict] = field(default_factory=dict)


def read_measured(paths: AppPaths, harness_ids: list[str]) -> Measured:
    if not paths.scoped_plan.is_file():
        return Measured(f"no_device_run: {paths.scoped_plan.relative_to(paths.root)} absent")
    plan = {r["id"]: r for r in read_yaml(paths.scoped_plan).get("scopes") or []}
    if sorted(plan) != sorted(harness_ids):
        raise ValueError(f"measured_mismatch: {paths.scoped_plan} lists scopes {sorted(plan)}, "
                         f"harness.yaml lists {sorted(harness_ids)}; rerun the device step on this harness")
    cases = {}
    if paths.scoped_benchmark.is_file():
        cases = {c["id"]: c for c in read_json(paths.scoped_benchmark).get("cases") or []}
    return Measured(None, plan, cases)
