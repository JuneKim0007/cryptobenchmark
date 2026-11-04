"""One scope's replacement turned into splices on its file, or the coded reason it cannot be."""
from __future__ import annotations

from ...dto.replacement import Replacement
from ...dto.site import Scope
from ...source.code import Code
from ...source.language import Language, of_file
from .algorithm import set_algorithm
from .locate import locate
from .parameters import pin_parameters
from .provider import set_provider
from .reject import Rejected
from .specs import Table
from .splice import Splice, apply

APPLY = {"set_provider": set_provider, "set_algorithm": set_algorithm, "pin_parameters": pin_parameters}


def language(file: str) -> Language:
    found = of_file(file)
    if found is None:
        raise Rejected("unsupported_language")
    return found


def plan(scope: Scope, replacement: Replacement, code: Code, table: Table) -> list[Splice]:
    if not replacement.edits:
        raise Rejected("no_edits")
    located = locate(code, scope)
    splices: list[Splice] = []
    for edit in replacement.edits:
        if edit.kind not in APPLY:
            raise Rejected("unsupported_kind")
        splices += APPLY[edit.kind](code, located, edit, table)
    if apply(code.text, splices) == code.text:
        raise Rejected("no_change")
    return splices
