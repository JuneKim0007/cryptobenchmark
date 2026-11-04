"""Whether a scope's function operates on its primitive, from tokens around the located call: a first filter, not data flow.

Refuses only what reads plainly as creating and handing back; a form it cannot read counts as an operation."""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from ..dto.site import Scope
from ..files import read_yaml
from ..source.brackets import CLOSE, OPEN, matching
from ..source.code import Code
from .dependencies import load
from .edit.init import BOUND
from .edit.locate import locate
from .edit.reject import Rejected

TABLE = Path(__file__).with_name("setup_calls.yaml")
_MEMBER = re.compile(r"\s*[?!]*\.\s*(\w+)\s*([({])")
_CALL = re.compile(r"(\w+)\s*[({]")
_RETURN_TYPE = re.compile(r"\)\s*:\s*$")
_RETURNED = re.compile(r"(?:\breturn|=)\s*$")
_BEFORE_ARGUMENT = re.compile(r"[(,]\s*$")
_AFTER_ARGUMENT = re.compile(r"\s*[,)]")
# a capitalised name is a constructor, Kotlin's without `new`
_OWN_CALL = re.compile(r"(?<![\w.])(new\s+)?([A-Za-z_]\w*)\s*\(")


@lru_cache(maxsize=1)
def _table() -> tuple[frozenset[str], frozenset[str]]:
    d = read_yaml(TABLE)
    return frozenset(d["setup"]), frozenset(d["blocks"])


def _top_level(masked: str, begin: int, end: int) -> str:
    """The text with everything inside a bracket blanked: an argument's call is not a call on the primitive."""
    out, depth = [], 0
    for ch in masked[begin:end]:
        depth -= ch in CLOSE
        out.append(ch if depth == 0 else " ")
        depth += ch in OPEN
    return "".join(out)


def _chain_operates(masked: str, at: int, end: int, skipped: frozenset[str]) -> bool:
    """`.a(..).b { .. }` from `at`; a block's top-level calls are on the primitive too."""
    setup, blocks = _table()
    while m := _MEMBER.match(masked, at, end):
        close = matching(masked, m.end() - 1)
        if close is None:
            return True
        if m.group(1) in blocks:
            inner = _top_level(masked, m.end(), close)
            if any(c.group(1) not in setup and c.group(1) not in skipped for c in _CALL.finditer(inner)):
                return True
        elif m.group(1) not in setup:
            return True
        at = close + 1
    return False


def _variable_operates(masked: str, name: str, after: int, end: int, skipped: frozenset[str]) -> bool:
    for m in re.compile(r"(?<![\w.])" + re.escape(name) + r"\b").finditer(masked, after, end):
        if _chain_operates(masked, m.end(), end, skipped):
            return True
        # handed to a call: a stream or helper may operate on it
        if _BEFORE_ARGUMENT.search(masked, after, m.start()) and _AFTER_ARGUMENT.match(masked, m.end(), end):
            return True
    return False


def _local(masked: str, name: str, begin: int, call: int, keywords: frozenset[str]) -> bool:
    """Declared in the function before the call, not a field."""
    declared = re.compile(r"([\w>\]?]+)\s+" + re.escape(name) + r"\b")
    return any(m.group(1) in {"val", "var"} or m.group(1) not in keywords for m in declared.finditer(masked, begin, call))


def _calls_own_method(masked: str, after: int, end: int, keywords: frozenset[str]) -> bool:
    return any(not m.group(1) and not m.group(2)[0].isupper() and m.group(2) not in keywords for m in _OWN_CALL.finditer(masked, after, end))


def has_operation(code: Code, scope: Scope) -> bool:
    try:
        located = locate(code, scope)
    except Rejected:
        return True
    masked, (begin, end) = code.masked, located.function
    after = located.args.close + 1
    skipped = load(code.language.name).keywords
    if _chain_operates(masked, after, end, skipped):
        return True
    bound = BOUND.search(masked, begin, located.call)
    # `fun f(): T = ...` binds no name: T is the return type
    if bound and not _RETURN_TYPE.search(masked, begin, bound.start()):
        name = bound.group(1)
        if _variable_operates(masked, name, after, end, skipped):
            return True
        # a field: another method this one calls may operate on it
        return not _local(masked, name, begin, located.call, skipped) and _calls_own_method(masked, after, end, skipped)
    return not _RETURNED.search(masked, begin, located.call)
