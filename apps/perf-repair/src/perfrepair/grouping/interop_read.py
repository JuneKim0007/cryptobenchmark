from __future__ import annotations

from pathlib import Path

import yaml

from cryptobench.paths import GroupingTree
from ..dto.interop import PairResult, not_checkable_results
from ..files import read_yaml, write_text
from ..validation import require
from ..validation.grouping.interop import validate_results


def imported(paths: GroupingTree) -> list[PairResult] | None:
    """The interop results grouping/ holds, checked against its plan; None before any import."""
    if not paths.interop.exists():
        return None
    results = read_yaml(paths.interop)
    plan = _plan(paths)
    require("grouping/interop.yaml", validate_results(results, plan))
    return [PairResult.from_interop(r) for r in results["pairs"]] + not_checkable_results(plan)


def import_results(paths: GroupingTree, source: Path) -> list[PairResult]:
    plan = _plan(paths)
    return write_results(paths, read_yaml(source), str(source), plan)


def write_results(paths: GroupingTree, results: dict, where: str = "grouping/interop.yaml",
                  plan: dict | None = None) -> list[PairResult]:
    require(where, validate_results(results, plan or _plan(paths)))
    write_text(paths.interop, yaml.safe_dump(results, sort_keys=False))
    return imported(paths)


def _plan(paths: GroupingTree) -> dict:
    require("grouping/interop_plan.yaml", [] if paths.interop_plan.exists() else
            [f"{paths.interop_plan} missing; run interop-plan before reading results"])
    return read_yaml(paths.interop_plan)
