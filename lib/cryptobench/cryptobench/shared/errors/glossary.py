"""Code: one code's default action, the actions `stops.<code>` may choose (none: fixed), exit code and next step."""
from __future__ import annotations

from dataclasses import dataclass

STOP, WARN, SKIP = "stop", "warn", "skip"
ACTIONS = (STOP, WARN, SKIP)
MIXES = "continuing would mix runs or devices"
NOTHING = "nothing is left to run"
UNUSABLE = "the input is unusable"
NOTICE = "a notice; nothing to choose"


@dataclass(frozen=True)
class Code:
    code: str
    action: str
    next: str
    allowed: tuple[str, ...] = ()
    # every code exits 1 today; argparse refuses its own errors with 2 before any code is reached
    exit: int = 1
    why: str = UNUSABLE

    @property
    def fixed(self) -> bool:
        return not self.allowed
