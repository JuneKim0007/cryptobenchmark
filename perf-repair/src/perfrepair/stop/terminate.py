"""terminate(): where a coded stop, warning or skip is decided: one event, then a Halt or the action to take."""
from __future__ import annotations

from ..dto.event import FINDING
from ..log import emit
from . import policy
from .codes import CODES, STOP
from .halt import Halt


def terminate(code: str, detail: str, *, stage: str, step: str, item: str | None = None, app: str | None = None,
              ref: str | None = None, data: dict | None = None, inner: str | None = None, trace: str = "") -> str:
    """Returns warn or skip; trace: lines the Halt's message carries and the status line leaves out."""
    c = CODES[code]
    chosen = policy.action(c)
    fields = {**(data or {}), "code": code, "action": chosen, "next": c.next, **({"inner": inner} if inner else {})}
    emit(stage, step, FINDING, item=item, app=app, outcome=chosen, ref=ref, detail=detail, data=fields)
    if chosen == STOP:
        raise Halt(code, detail + trace, c.next, c.exit, inner)
    return chosen
