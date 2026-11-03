"""The failures every command reports as one `error ...` line and exit 1, instead of a traceback."""
from __future__ import annotations

import logging
import sys
import traceback
from typing import Callable

from .ai.runtime.agent.reply import AgentFailed
from .app.facts.gate import GateError
from .data_handler.outbound.benchmark_runner import BenchmarkRunError
from .dto.event import BUG, ERROR
from .log import bug_log, command_run, emit
from .validation.failure import ValidationFailed

# ValueError covers JSON and YAML parse errors and every coded error (InputError, CatalogMismatch, ...)
FAILURES = (ValidationFailed, ValueError, OSError, GateError, BenchmarkRunError, AgentFailed)


def record_bug(e: Exception) -> None:
    """Anything not coded is a bug: its traceback goes to bug.log, or to stderr before the device folder is known."""
    trace = traceback.format_exc()
    emit("run", "bug", BUG, outcome="bug", detail=f"{type(e).__name__}: {e}", data={"traceback": trace},
         level=logging.ERROR)
    where = bug_log()
    print(f"error bug: {type(e).__name__}: {e}" + (f"; traceback in {where}" if where else ""), file=sys.stderr)
    if where is None:
        print(trace, file=sys.stderr, end="")


def reported(step: Callable[[], object]) -> int:
    """step's exit code when it returns one, else 0; a FAILURES exception is `error <it>` on stderr and 1."""
    with command_run() as run:
        try:
            code = step()
        except FAILURES as e:
            emit("run", "error", ERROR, outcome="error", detail=str(e))
            print(f"error {e}", file=sys.stderr)
            run.outcome = "error"
            return 1
        except Exception as e:
            record_bug(e)
            run.outcome = "bug"
            return 1
        code = code if isinstance(code, int) else 0
        run.outcome = "ok" if code == 0 else f"exit {code}"
        return code
