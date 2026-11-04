"""set_algorithm: the call's literal algorithm argument rewritten to `edit.algorithm`."""
from __future__ import annotations

from ...dto.replacement import Edit
from ...source.code import Code
from .literal import string_literal
from .locate import Located
from .reject import Rejected
from .specs import Table
from .splice import Splice


def set_algorithm(code: Code, located: Located, edit: Edit, table: Table) -> list[Splice]:
    """A constant's declaration is never edited: other code may read it."""
    if edit.parameters:
        raise Rejected("unknown_parameters")
    if not isinstance(edit.algorithm, str) or not edit.algorithm:
        raise Rejected("missing_parameter")
    if not located.args.spans:
        raise Rejected("unsupported_expression")
    start, end = located.args.spans[0]
    if not code.is_literal(start, end):
        raise Rejected("algorithm_not_literal")
    return [Splice(start, end, string_literal(edit.algorithm, code.language))]
