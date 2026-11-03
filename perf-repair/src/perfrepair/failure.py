"""The failures every command reports as one `error ...` line and its code's exit, instead of a traceback."""
from __future__ import annotations

import logging
import sys
import traceback
from dataclasses import dataclass
from typing import Callable

from .ai.runtime.agent.reply import AgentFailed
from .app.facts.gate import GateError
from .data_handler.outbound.benchmark_runner import BenchmarkRunError
from .dto.event import BUG, ERROR
from .log import bug_log, command_run, emit
from .log.attach import nested
from .stop import CODES, Halt, code_of
from .validation.failure import ValidationFailed

# ValueError covers JSON and YAML parse errors and every coded error (InputError, CatalogMismatch, ...)
FAILURES = (Halt, ValidationFailed, ValueError, OSError, GateError, BenchmarkRunError, AgentFailed)


@dataclass(frozen=True)
class Failed:
    code: str | None
    detail: str


_last: Failed | None = None


def last_failure() -> Failed | None:
    """The coded failure of the last command run in-process, taken once: its caller's line carries it."""
    global _last
    found, _last = _last, None
    return found


def record_bug(e: Exception) -> None:
    """Anything not coded is a bug: its traceback goes to bug.log, or to stderr before the device folder is known."""
    trace = traceback.format_exc()
    emit("run", "bug", BUG, outcome="bug", detail=f"{type(e).__name__}: {e}", data={"traceback": trace},
         level=logging.ERROR)
    where = bug_log()
    print(f"error bug: {type(e).__name__}: {e}" + (f"; traceback in {where}" if where else ""), file=sys.stderr)
    if where is None:
        print(trace, file=sys.stderr, end="")


def _failed(e: Exception) -> int:
    """A Halt's event is written; another coded failure is one error event, left to the caller when it runs in-process."""
    global _last
    code = code_of(e)
    if not isinstance(e, Halt) and not nested():
        emit("run", "error", ERROR, outcome="error", detail=str(e), data={"code": code} if code else {})
    print(f"error {e}", file=sys.stderr)
    _last = Failed(code, e.detail if isinstance(e, Halt) else str(e))
    return e.exit if isinstance(e, Halt) else CODES[code].exit if code in CODES else 1


def reported(step: Callable[[], object]) -> int:
    """step's exit code when it returns one, else 0; a FAILURES exception is `error <it>` on stderr and its code's exit."""
    with command_run() as run:
        try:
            code = step()
        except FAILURES as e:
            run.outcome = "error"
            return _failed(e)
        except Exception as e:
            record_bug(e)
            run.outcome = "bug"
            return 1
        code = code if isinstance(code, int) else 0
        run.outcome = "ok" if code == 0 else f"exit {code}"
        return code
