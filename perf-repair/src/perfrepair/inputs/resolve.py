"""One input from an ordered chain of sources: an unset value falls through; a set one that fails follows its policy."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Iterable

from .check import Invalid

LOG = logging.getLogger("perfrepair.inputs")
CLI = "cli"


class Need(Enum):
    REQUIRED = "required"
    DEFAULT = "default"
    OPTIONAL = "optional"


class OnInvalid(Enum):
    USE_DEFAULT = "use the default"
    ERROR = "error"


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


def unknown_key(where: str, known: Iterable[Any], origin: str) -> None:
    LOG.warning(f"unknown_key: {where}, known {list(known)} ({origin})",
                extra={"code": "unknown_key", "input": where, "source": origin})


def choose(name: str, candidates: Iterable[Candidate], check: Callable[[str, Any], None],
           on_invalid: OnInvalid) -> Candidate | None:
    """The first set candidate. A bad flag or an ERROR row raises; a bad file or environment value warns and takes the default."""
    candidates = list(candidates)
    for c in candidates:
        if c.value is None:
            continue
        try:
            check(name, c.value)
        except Invalid as e:
            if on_invalid is OnInvalid.ERROR or c.source == CLI or not c.explicit:
                raise InputError("invalid", f"{name} {c.value}, {e.expected} ({c.source})") from None
            default = next((d for d in candidates if not d.explicit and d.value is not None), None)
            using = f"using the default {default.value}" if default else "ignored"
            LOG.warning(f"invalid: {name} {c.value}, {e.expected}; {using} ({c.source})",
                        extra={"code": "invalid", "input": name, "source": c.source})
            return default
        return c
    return None


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
