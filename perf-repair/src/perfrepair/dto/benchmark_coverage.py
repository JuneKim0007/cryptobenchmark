"""log/details/benchmark_coverage.yaml (schema 1): per used item and planned configuration and metric, measured or a gap
of one class; each class's action, the attempt count, the totals."""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass

SCHEMA_VERSION = 1
MEASURED = "measured"
NEVER_PLANNED, LOST, PARTIAL, LOW_QUALITY = "never_planned", "lost", "partial", "low_quality"
REPEATS, REFUSED, NO_OPERATION = "repeats", "refused", "no_operation"
DELTA, CODED = "delta", "coded"
# the design's table: what each gap class does; a delta one is measured again, a coded one keeps its reason
ACTIONS = {NEVER_PLANNED: DELTA, LOST: DELTA, PARTIAL: DELTA, LOW_QUALITY: DELTA, REPEATS: CODED, REFUSED: CODED,
           NO_OPERATION: CODED}
CLASSES = tuple(ACTIONS)
POINTS = ("used", "grouped")
# device.benchmark.onGap and onSetupMismatch: a whole rerun starts only when the second is rerun
GAP_DELTA, GAP_STOP, SETUP_STOP, SETUP_RERUN = "delta", "stop", "stop", "rerun"
ON_GAP, ON_SETUP_MISMATCH = (GAP_DELTA, GAP_STOP), (SETUP_STOP, SETUP_RERUN)
ANY = "*"


@dataclass(frozen=True)
class Gap:
    """One key without a usable measurement; operation, variant and metric are `*` for an item nothing planned."""
    item: str
    operation: str
    variant: str
    keySize: int | None
    inputSize: int | None
    metric: str
    gap: str
    reason: str
    case: str | None = None

    @property
    def action(self) -> str:
        return ACTIONS[self.gap]

    @property
    def key(self) -> tuple:
        return self.item, self.operation, self.variant, self.keySize, self.inputSize, self.metric

    def to_json(self) -> dict:
        return {**asdict(self), "action": self.action}


@dataclass(frozen=True)
class Coverage:
    """measured: the keys with a usable measurement; items: per used item measured, or its worst gap class."""
    used: tuple[str, ...]
    measured: int
    gaps: tuple[Gap, ...]

    def delta(self) -> tuple[Gap, ...]:
        return tuple(g for g in self.gaps if g.action == DELTA)

    def coded(self) -> tuple[Gap, ...]:
        return tuple(g for g in self.gaps if g.action == CODED)

    def items(self) -> dict[str, str]:
        worst = {}
        for g in self.gaps:
            if g.item not in worst or CLASSES.index(g.gap) < CLASSES.index(worst[g.item]):
                worst[g.item] = g.gap
        return {i: worst.get(i, MEASURED) for i in self.used}

    def totals(self) -> dict:
        classes = Counter(g.gap for g in self.gaps)
        return {"usedItems": len(self.used), "itemsMeasured": sum(s == MEASURED for s in self.items().values()),
                "keysMeasured": self.measured, "gaps": len(self.gaps), **{c: classes.get(c, 0) for c in CLASSES}}


def coverage_document(run: str, point: str, attempt: int, coverage: Coverage, delta: dict | None = None) -> dict:
    return {"schemaVersion": SCHEMA_VERSION, "run": run, "point": point, "attempt": attempt, "totals": coverage.totals(),
            "items": coverage.items(), "gaps": [g.to_json() for g in coverage.gaps], "delta": delta or {}}
