"""The glossary, codes.yaml: every code once with its kind, and its default action where a reader resolves it;
Code: a code's stops.<code> entry, its default action, the actions `stops.<code>` may choose (none: fixed), exit code,
next step and why."""
from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from importlib import resources

import yaml

STOP = "stop"


@dataclass(frozen=True)
class Code:
    code: str
    action: str
    next: str
    allowed: tuple[str, ...]
    exit: int
    why: str

    @property
    def fixed(self) -> bool:
        return not self.allowed


@cache
def codes() -> dict[str, dict]:
    """Each code's entry, in the file's order."""
    return yaml.safe_load(resources.files(__package__).joinpath("codes.yaml").read_text(encoding="utf-8"))["codes"]


def stops() -> tuple[Code, ...]:
    """The codes perf-repair's stops.<code> addresses, in the file's order."""
    return tuple(Code(name, e["default"], s["next"], tuple(s["settable"]), s["exit"], s["why"])
                 for name, e in codes().items() if (s := e.get("stops")))
