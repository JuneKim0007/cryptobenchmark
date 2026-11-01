"""One scope's replacement turned into splices on its file, or the coded reason it cannot be."""
from __future__ import annotations

from ...dto.site import Replacement, Scope
from .algorithm import set_algorithm
from .lexer import LANGUAGES, Source
from .locate import locate
from .parameters import pin_parameters
from .provider import set_provider
from .reject import Rejected
from .specs import Table
from .splice import Splice, apply


def language(file: str) -> str:
    suffix = file[file.rfind("."):] if "." in file else ""
    if suffix not in LANGUAGES:
        raise Rejected("unsupported_language")
    return LANGUAGES[suffix]


def plan(scope: Scope, replacement: Replacement, source: Source, table: Table) -> list[Splice]:
    lang = language(scope.file)
    if not replacement.edits:
        raise Rejected("no_edits")
    located = locate(source, scope)
    splices: list[Splice] = []
    for edit in replacement.edits:
        if edit.kind == "set_provider":
            splices.append(set_provider(source, located, edit, lang))
        elif edit.kind == "set_algorithm":
            splices.append(set_algorithm(source, located, edit, lang))
        elif edit.kind == "pin_parameters":
            splices += pin_parameters(source, located, edit, lang, table)
        else:
            raise Rejected("unsupported_kind")
    if apply(source.text, splices) == source.text:
        raise Rejected("no_change")
    return splices
