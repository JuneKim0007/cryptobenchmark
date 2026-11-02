"""One input from an ordered chain of sources: a set value that fails is an error, an unset one falls through."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Iterable

LOG = logging.getLogger("perfrepair.inputs")


class Need(Enum):
    REQUIRED = "required"
    DEFAULT = "default"
    OPTIONAL = "optional"


class InputError(ValueError):

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code


@dataclass(frozen=True)
class Candidate:
    value: Any
    source: str
    explicit: bool = True
    note: str = ""


@dataclass(frozen=True)
class Resolved:
    value: Any
    source: str


def _log(name: str, code: str, source: str, text: str) -> None:
    LOG.info(f"{name}: {text}", extra={"code": code, "input": name, "source": source})


def resolve(name: str, candidates: Iterable[Candidate], load: Callable[[Any], Any], need: Need,
            null: Any = None) -> Resolved:
    candidates = list(candidates)
    for c in candidates:
        if c.value is None:
            continue
        try:
            loaded = load(c.value)
        except OSError as e:
            if c.explicit:
                raise InputError("missing_file", f"{name}: {c.value} ({c.source}): {e.strerror or e}") from None
            continue
        if not c.explicit:
            _log(name, "default", c.source, f"{c.source} {c.note}".rstrip())
        return Resolved(loaded, c.source)
    tried = ", ".join(c.source for c in candidates) or "no source"
    if need is Need.OPTIONAL:
        _log(name, "not_found", "none", f"not found ({tried}); skipped")
        return Resolved(null, "none")
    raise InputError("missing_input", f"{name}: nothing found ({tried})")
