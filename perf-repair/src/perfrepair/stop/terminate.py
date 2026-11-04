"""terminate(): where a coded stop, warning or skip is decided: one event, then a Halt or the action to take."""
from __future__ import annotations

from ..dto.event import FINDING
from ..log import emit
from . import policy
from .codes import CODES, STOP
from .halt import Halt


def terminate(code: str, detail: str, *, stage: str, step: str, item: str | None = None, app: str | None = None,
              ref: str | None = None, data: dict | None = None, inner: str | None = None, trace: str = "",
              next_step: str | None = None) -> str:
    """Returns warn or skip; trace: lines the Halt's message carries and the status line leaves out; next_step: what this
    cause calls for, when the code's own next cannot know it."""
    c = CODES[code]
    chosen = policy.action(c)
    next_step = next_step or c.next
    fields = {**(data or {}), "code": code, "action": chosen, "next": next_step, **({"inner": inner} if inner else {})}
    emit(stage, step, FINDING, item=item, app=app, outcome=chosen, ref=ref, detail=detail, data=fields)
    if chosen == STOP:
        raise Halt(code, detail + trace, next_step, c.exit, inner)
    return chosen


def halt_of(code: str, detail: str, **where) -> Halt:
    """A fixed stop terminated and its Halt handed back, for a caller that records it instead of raising it."""
    if not CODES[code].fixed or CODES[code].action != STOP:
        raise ValueError(f"{code} is not a fixed stop")
    try:
        terminate(code, detail, **where)
    except Halt as h:
        return h
    raise ValueError(f"{code} did not stop")
