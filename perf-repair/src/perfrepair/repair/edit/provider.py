"""set_provider: the call's provider argument rewritten, or appended when the call has none."""
from __future__ import annotations

import re

from ...app.lexer import Code
from ...dto.site import Edit
from .literal import string_literal
from .locate import Located
from .reject import Rejected
from .specs import Table
from .splice import Splice

_GET_PROVIDER = re.compile(r'(?:\w+\s*\.\s*)*getProvider\s*\(\s*("(?:[^"\\\n]|\\.)*")\s*\)')


def set_provider(code: Code, located: Located, edit: Edit, table: Table) -> list[Splice]:
    if not edit.provider:
        raise Rejected("missing_parameter")
    new = string_literal(edit.provider, code.language)
    spans = located.args.spans
    if len(spans) == 1:
        return [Splice(spans[0][1], spans[0][1], f", {new}")]
    if len(spans) != 2:
        raise Rejected("unsupported_expression")
    start, end = spans[1]
    if code.is_literal(start, end):
        return [Splice(start, end, new)]
    m = _GET_PROVIDER.fullmatch(code.text, start, end)
    if m and code.is_literal(*m.span(1)):
        return [Splice(*m.span(1), new)]
    raise Rejected("unsupported_expression")
