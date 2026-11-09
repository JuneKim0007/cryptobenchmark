"""cryptobenchmark's --harness output for one app: each scope's scoped-plan record, its compile and interop verdict."""
from __future__ import annotations

from dataclasses import dataclass, field

from cryptobench.paths import AppTree
from ..files import read_yaml
from ..stop.halt import Coded


@dataclass(frozen=True)
class DeviceCheck:
    """`absent` says why there is no plan."""
    absent: str | None
    plan: dict[str, dict] = field(default_factory=dict)


def read_device_check(paths: AppTree, harness_ids: list[str]) -> DeviceCheck:
    if not paths.scoped_plan.is_file():
        return DeviceCheck(f"no_device_run: {paths.scoped_plan.relative_to(paths.root)} absent")
    plan = {r["id"]: r for r in read_yaml(paths.scoped_plan).get("scopes") or []}
    if sorted(plan) != sorted(harness_ids):
        raise Coded(f"scoped_plan_mismatch: {paths.scoped_plan} lists scopes {sorted(plan)}, "
                         f"harness.yaml lists {sorted(harness_ids)}; rerun the device step on this harness")
    return DeviceCheck(None, plan)
