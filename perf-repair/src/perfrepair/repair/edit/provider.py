"""set_provider: the call's provider argument rewritten, or appended when the call has none."""
from __future__ import annotations

import re

from ...dto.site import Edit
from .lexer import Source
from .literal import string_literal
from .locate import Located
from .reject import Rejected
from .splice import Splice

_GET_PROVIDER = re.compile(r'(?:\w+\s*\.\s*)*getProvider\s*\(\s*("(?:[^"\\\n]|\\.)*")\s*\)')


def set_provider(source: Source, located: Located, edit: Edit, language: str) -> Splice:
    if not edit.provider:
        raise Rejected("missing_parameter")
    new = string_literal(edit.provider, language)
    spans = located.args.spans
    if len(spans) == 1:
        return Splice(spans[0][1], spans[0][1], f", {new}")
    if len(spans) != 2:
        raise Rejected("unsupported_expression")
    start, end = spans[1]
    if source.is_literal(start, end):
        return Splice(start, end, new)
    m = _GET_PROVIDER.fullmatch(source.text, start, end)
    if m and source.is_literal(*m.span(1)):
        return Splice(*m.span(1), new)
    raise Rejected("unsupported_expression")
