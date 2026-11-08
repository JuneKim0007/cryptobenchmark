"""The configurations an option is estimated at: those nearest the scope, the pins they show, and per metric the estimate."""
from __future__ import annotations

import re
from typing import NamedTuple

from ..dto import PrimitiveRow, Summary
from ..dto.dossier import SETUP_DRIFT, TOO_FEW_RUNS, Estimate, NoEstimate, reason_code
from ..dto.measurement import ESTIMATED
from ..dto.metrics import BY_NAME
from ..dto.site import Scope
from .estimate import MIN_RUNS, Comparison, compare

ESTIMATED_SUFFIX = ", estimated"
LABEL = re.compile(rf"^(?P<op>\S+) key (?P<key>\S+) input (?P<input>\S+) (?P<phase>\S+)(?P<estimated>{ESTIMATED_SUFFIX})?$")


class Config(NamedTuple):
    operation: str
    keySize: int | None
    inputSize: int | None
    phase: str


def config_of(r: PrimitiveRow) -> Config:
    return Config(r.operation, r.keySize, r.inputSize, r.phase)


def label(c: Config) -> str:
    return f"{c.operation} key {c.keySize} input {c.inputSize} {c.phase}"


def parse_label(text: str) -> re.Match | None:
    """label()'s fields back from a stored configuration; `estimated` when the side's energy is estimated."""
    return LABEL.match(text)


def _order(c: Config) -> str:
    return str(tuple(c))


def nearest(scope: Scope, current: dict[Config, PrimitiveRow], option: dict[Config, PrimitiveRow],
            operations: tuple[str, ...] = ()) -> list[Config]:
    """Configurations both measured at the scope's key size and the closest input size; every size when unknown.
    operations: only these, when given."""
    shared = [c for c in current if c in option and scope.keySize in (None, c.keySize)
              and (not operations or c.operation in operations)]
    if scope.inputSize is None or not shared:
        return sorted(shared, key=_order)
    gap = min(abs((c.inputSize or 0) - scope.inputSize) for c in shared)
    return sorted((c for c in shared if abs((c.inputSize or 0) - scope.inputSize) == gap), key=_order)


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
                yield c, metric, _compared(current[c], option[c], before, after, metric), after.kind


def _compared(mine: PrimitiveRow, theirs: PrimitiveRow, before: Summary, after: Summary, metric: str) -> Comparison:
    if mine.session != theirs.session and (mine.drift or theirs.drift):
        return Comparison(None, None, 0, f"{SETUP_DRIFT}: {mine.session or 'benchmark'} and {theirs.session or 'benchmark'}")
    if min(before.n, after.n) < MIN_RUNS:
        return Comparison(None, None, 0, f"{TOO_FEW_RUNS}: {before.n} and {after.n} runs, an estimate needs {MIN_RUNS}")
    return compare(before, after, BY_NAME[metric].lowerIsBetter)


def cross_session(configs: list[Config], current: dict[Config, PrimitiveRow], option: dict[Config, PrimitiveRow]) -> bool:
    """The two sides of a shown configuration were measured in different sessions; the dossier says so."""
    return any(current[c].session != option[c].session for c in configs)


def _shown(c: Config, kind: str | None) -> str:
    # the words reach the decision through the configuration it is already shown
    return f"{label(c)}{ESTIMATED_SUFFIX}" if kind == ESTIMATED else label(c)


def estimates(*sides) -> tuple[tuple[Estimate, ...], tuple[NoEstimate, ...]]:
    """Each metric both sides have: an estimate, or the reason code compare() gives no ratio, so the decision sees why."""
    found = list(_sides(*sides))
    return (tuple(Estimate(metric, e.ratio, e.pImprove, e.n, _shown(c, kind), kind) for c, metric, e, kind in found
                  if e.ratio is not None),
            tuple(NoEstimate(metric, label(c), reason_code(e.reason)) for c, metric, e, _ in found if e.ratio is None))
