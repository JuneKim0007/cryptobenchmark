"""A scope's divergence category by a fixed rule over its lifecycle, with the lines that decided it."""
from __future__ import annotations

from typing import NamedTuple

from ..dto.lifecycle import BOUNDED, PARTIALLY_BOUNDED, Lifecycle
from ..dto.pattern import CREATED_PER_CALL, HELD_IN_FIELD, UNKNOWN_DEFAULT, pattern_of_reason

_USES = ("use", "consume")
# (bindings, the partial reasons the rule tolerates)
_PER_CALL = (("local", "chain"), {"wrapper", "depth1"})
_HELD = (("field",), {"field", "depth1"})


class Pattern(NamedTuple):
    pattern: str
    reason: str
    lines: tuple[int, ...]


def _of(reason: str, lines: tuple[int, ...]) -> Pattern:
    return Pattern(pattern_of_reason(reason), reason, lines)


def _reads(lc: Lifecycle, rule: tuple) -> bool:
    bindings, reasons = rule
    return lc.binding in bindings and set(lc.reasons) <= reasons


def pattern_of(lc: Lifecycle | None, line: int) -> Pattern:
    """An escape, a deferred use, a cut budget or a step not found leaves the setup's place open: unknown_default."""
    if lc is None or lc.status not in (BOUNDED, PARTIALLY_BOUNDED):
        return _of(UNKNOWN_DEFAULT, (line,))
    uses = [s for s in lc.steps if s.role in _USES]
    lines = tuple(sorted({line, *(s.line for s in lc.steps if s.role == "configure" or s.role in _USES)}))
    if uses and _reads(lc, _PER_CALL):
        return _of(CREATED_PER_CALL, lines)
    # a use beside the creation could be a lazy cache or a re-creation per call; the reading cannot tell
    if uses and _reads(lc, _HELD) and all(s.where == "depth1" for s in uses):
        return _of(HELD_IN_FIELD, lines)
    return _of(UNKNOWN_DEFAULT, lines)
