"""set_algorithm: the call's literal algorithm argument rewritten to `parameters["algorithm"]`."""
from __future__ import annotations

from ...dto.site import Edit
from .lexer import Source
from .literal import string_literal
from .locate import Located
from .reject import Rejected
from .splice import Splice


def set_algorithm(source: Source, located: Located, edit: Edit, language: str) -> Splice:
    """A constant's declaration is never edited: other code may read it."""
    parameters = edit.parameters or {}
    if set(parameters) - {"algorithm"}:
        raise Rejected("unknown_parameters")
    if not isinstance(parameters.get("algorithm"), str) or not parameters["algorithm"]:
        raise Rejected("missing_parameter")
    if not located.args.spans:
        raise Rejected("unsupported_expression")
    start, end = located.args.spans[0]
    if not source.is_literal(start, end):
        raise Rejected("algorithm_not_literal")
    return Splice(start, end, string_literal(parameters["algorithm"], language))
