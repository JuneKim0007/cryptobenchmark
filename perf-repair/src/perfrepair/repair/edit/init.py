"""The one `init` call on the engine a scope's call returns, inside the scope's function; never guessed."""
from __future__ import annotations

import re

from ...source.lexer import Arguments, Code, matching
from .locate import Located, call_arguments
from .reject import Rejected

_BOUND = re.compile(r"\b([A-Za-z_]\w*)\s*(?::\s*[\w.<>?, ]+?)?\s*=\s*$")
_RECEIVER_BLOCK = re.compile(r"\s*\.\s*(?:apply|run)\s*\{")
_BARE_INIT = re.compile(r"(?<![\w.])init\s*\(")


def _only(starts: list[int], code: Code) -> Arguments:
    if not starts:
        raise Rejected("no_init")
    if len(starts) > 1:
        raise Rejected("ambiguous_init")
    return call_arguments(code, starts[0])


def find_init(code: Code, located: Located) -> Arguments:
    """`v = X.getInstance(..)` then `v.init(..)`, or Kotlin `X.getInstance(..).apply { init(..) }`."""
    masked = code.masked
    begin, end = located.function
    after = located.args.close + 1
    block = _RECEIVER_BLOCK.match(masked, after)
    if block:
        close = matching(masked, block.end() - 1)
        if close is None:
            raise Rejected("unbalanced_call")
        return _only([m.end() - 1 for m in _BARE_INIT.finditer(masked, block.end(), close)], code)
    bound = _BOUND.search(masked, begin, located.call)
    if not bound:
        raise Rejected("no_init")
    call = re.compile(r"\b" + re.escape(bound.group(1)) + r"\s*\.\s*init\s*\(")
    return _only([m.end() - 1 for m in call.finditer(masked, after, end)], code)
