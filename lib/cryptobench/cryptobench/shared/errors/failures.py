"""The coded failures one package raises and another reports: each keeps its own base, so `except ValueError` misses it."""
from __future__ import annotations

from .coded import Coded, code_in


class AgentFailed(RuntimeError):
    """The provider failed for a reason that is not a refusal; one coded line."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {' '.join(detail.split())}")
        self.code = code


class GateError(Exception):
    def __init__(self, reason: str, detail: str):
        super().__init__(f"{reason}: {detail}")
        self.reason = self.code = reason


class BenchmarkRunError(RuntimeError):
    """Often the child's own last line, so its code can only be read from those words."""

    def __init__(self, message: str):
        super().__init__(message)
        self.code = code_in(message)


class EnergyError(Coded):
    """Raised by the energy sources, reported by the runner."""


class CommandError(Coded):
    """Raised by the runner's library code, reported by its entry point as one `error:` line and exit 1, never a traceback."""
