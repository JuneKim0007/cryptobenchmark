"""The failures every command reports as one `error ...` line and exit 1, instead of a traceback."""
from __future__ import annotations

import sys
from typing import Callable

from .ai.runtime.agent.claude_code import ClaudeCodeError
from .app.gate import GateError
from .data_handler.outbound.benchmark_runner import BenchmarkRunError
from .validation.failure import ValidationFailed

# ValueError covers JSON and YAML parse errors and every coded error (InputError, CatalogMismatch, ...)
FAILURES = (ValidationFailed, ValueError, OSError, GateError, BenchmarkRunError, ClaudeCodeError)


def reported(step: Callable[[], object]) -> int:
    """step's exit code when it returns one, else 0; a FAILURES exception is `error <it>` on stderr and 1."""
    try:
        code = step()
    except FAILURES as e:
        print(f"error {e}", file=sys.stderr)
        return 1
    return code if isinstance(code, int) else 0
