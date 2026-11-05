"""cryptobenchmark's --harness output for one app: each scope's scoped-plan record, its compile and interop verdict."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..files import read_yaml
from ..run_dir import AppPaths
from ..stop.halt import Coded


@dataclass(frozen=True)
class Measured:
    """`absent` says why there is no plan."""
    absent: str | None
    plan: dict[str, dict] = field(default_factory=dict)


def read_measured(paths: AppPaths, harness_ids: list[str]) -> Measured:
    if not paths.scoped_plan.is_file():
        return Measured(f"no_device_run: {paths.scoped_plan.relative_to(paths.root)} absent")
    plan = {r["id"]: r for r in read_yaml(paths.scoped_plan).get("scopes") or []}
    if sorted(plan) != sorted(harness_ids):
        raise Coded(f"measured_mismatch: {paths.scoped_plan} lists scopes {sorted(plan)}, "
                         f"harness.yaml lists {sorted(harness_ids)}; rerun the device step on this harness")
    return Measured(None, plan)
