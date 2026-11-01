"""The one `init` call on the engine a scope's call returns, inside the scope's function; never guessed."""
from __future__ import annotations

import re

from .calls import Arguments, arguments
from .lexer import Source
from .locate import Located
from .reject import Rejected

_BOUND = re.compile(r"\b([A-Za-z_]\w*)\s*(?::\s*[\w.<>?, ]+?)?\s*=\s*$")
_RECEIVER_BLOCK = re.compile(r"\s*\.\s*(?:apply|run)\s*\{")
_BARE_INIT = re.compile(r"(?<![\w.])init\s*\(")


def _block_end(masked: str, open_: int) -> int:
    depth = 0
    for i in range(open_, len(masked)):
        depth += {"{": 1, "}": -1}.get(masked[i], 0)
        if depth == 0:
            return i
    raise Rejected("unbalanced_call")


def _only(starts: list[int], masked: str) -> Arguments:
    if not starts:
        raise Rejected("no_init")
    if len(starts) > 1:
        raise Rejected("ambiguous_init")
    return arguments(masked, starts[0])


def find_init(source: Source, located: Located) -> Arguments:
    """`v = X.getInstance(..)` then `v.init(..)`, or Kotlin `X.getInstance(..).apply { init(..) }`."""
    masked = source.masked
    begin, end = located.function
    after = located.args.close + 1
    block = _RECEIVER_BLOCK.match(masked, after)
    if block:
        close = _block_end(masked, block.end() - 1)
        return _only([m.end() - 1 for m in _BARE_INIT.finditer(masked, block.end(), close)], masked)
    bound = _BOUND.search(masked, begin, located.call)
    if not bound:
        raise Rejected("no_init")
    call = re.compile(r"\b" + re.escape(bound.group(1)) + r"\s*\.\s*init\s*\(")
    return _only([m.end() - 1 for m in call.finditer(masked, after, end)], masked)
