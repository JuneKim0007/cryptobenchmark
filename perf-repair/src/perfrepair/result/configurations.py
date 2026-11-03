"""The configurations an option is estimated at: those nearest the scope, the pins they show, and per metric the estimate."""
from __future__ import annotations

from ..dto import PrimitiveRow, Summary
from ..dto.measurement import ESTIMATED
from ..dto.metrics import BY_NAME
from ..dto.site import Estimate, NoEstimate, Scope, reason_code
from .estimate import compare

Config = tuple  # (operation, keySize, inputSize, phase)


def config_of(r: PrimitiveRow) -> Config:
    return r.operation, r.keySize, r.inputSize, r.phase


def label(c: Config) -> str:
    return f"{c[0]} key {c[1]} input {c[2]} {c[3]}"


def nearest(scope: Scope, current: dict[Config, PrimitiveRow], option: dict[Config, PrimitiveRow],
            operations: tuple[str, ...] = ()) -> list[Config]:
    """Configurations both measured at the scope's key size and the closest input size; every size when unknown.
    operations: only these, when given."""
    shared = [c for c in current if c in option and scope.keySize in (None, c[1]) and (not operations or c[0] in operations)]
    if scope.inputSize is None or not shared:
        return sorted(shared, key=str)
    gap = min(abs((c[2] or 0) - scope.inputSize) for c in shared)
    return sorted((c for c in shared if abs((c[2] or 0) - scope.inputSize) == gap), key=str)


def operations(scope: Scope) -> tuple[str, ...]:
    """The operations the lifecycle performs; empty, meaning every one, when it does not know."""
    return scope.lifecycle.operations if scope.lifecycle is not None else ()


def pins(current: PrimitiveRow, option: PrimitiveRow) -> dict:
    """The option's parameters that differ from the current ones."""
    keys = sorted(set(current.parameters) | set(option.parameters))
    return {k: option.parameters.get(k) for k in keys if current.parameters.get(k) != option.parameters.get(k)}


def _sides(configs: list[Config], current: dict[Config, PrimitiveRow], option: dict[Config, PrimitiveRow],
           measurements: dict[str, dict[str, Summary | None]], metrics: tuple[str, ...]):
    for c in configs:
        for metric in metrics:
            before = (measurements.get(current[c].rowId) or {}).get(metric)
            after = (measurements.get(option[c].rowId) or {}).get(metric)
            if before is not None and after is not None:
                yield c, metric, compare(before, after, BY_NAME[metric].lowerIsBetter), after.kind


def _shown(c: Config, kind: str | None) -> str:
    # the words reach the decision through the configuration it is already shown
    return f"{label(c)}, estimated" if kind == ESTIMATED else label(c)


def estimates(*sides) -> tuple[tuple[Estimate, ...], tuple[NoEstimate, ...]]:
    """Each metric both sides have: an estimate, or the reason code compare() gives no ratio, so the decision sees why."""
    found = list(_sides(*sides))
    return (tuple(Estimate(metric, e.ratio, e.pImprove, e.n, _shown(c, kind), kind) for c, metric, e, kind in found
                  if e.ratio is not None),
            tuple(NoEstimate(metric, label(c), reason_code(e.reason)) for c, metric, e, _ in found if e.ratio is None))
