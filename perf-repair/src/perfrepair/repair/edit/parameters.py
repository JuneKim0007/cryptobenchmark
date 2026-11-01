"""pin_parameters: the scope's init gets the parameter spec specs.yaml renders, or its existing spec's pinned fields."""
from __future__ import annotations

import re

from ...dto.site import Edit
from .calls import Arguments, arguments
from .init import find_init
from .lexer import Source
from .locate import Located
from .reject import Rejected
from .specs import Spec, Table
from .splice import Splice

_CONSTRUCTOR = re.compile(r"(?:new\s+)?((?:\w+\s*\.\s*)*\w+)\s*\(")


def _existing(source: Source, init: Arguments, table: Table, spec: Spec) -> Arguments | None:
    """The init's argument at the spec position when it constructs `spec` with the table's arity."""
    if len(init.spans) == table.position:
        return None
    if len(init.spans) <= table.position:
        raise Rejected("unsupported_expression")
    start, end = init.spans[table.position]
    m = _CONSTRUCTOR.match(source.masked, start, end)
    if not m or re.sub(r"\s", "", m.group(1)).rsplit(".", 1)[-1] != spec.simple_name:
        raise Rejected("unsupported_expression")
    args = arguments(source.masked, m.end() - 1)
    if args.close + 1 != end or len(args.spans) != len(spec.args):
        raise Rejected("unsupported_expression")
    return args


def _encrypting(source: Source, init: Arguments, table: Table) -> bool:
    mode = re.sub(r"\s", "", source.masked[slice(*init.spans[0])])
    return mode.rsplit(".", 1)[-1] in table.encrypting_modes


def pin_parameters(source: Source, located: Located, edit: Edit, language: str, table: Table) -> list[Splice]:
    pins = dict(edit.parameters or {})
    spec = table.spec_for(set(pins))
    init = find_init(source, located)
    existing = _existing(source, init, table, spec)
    if any(f.type == "random_bytes" and f.field in pins for f in spec.args):
        if existing is not None or not _encrypting(source, init, table):
            raise Rejected("unsupported_expression")
    if existing is not None:
        return [Splice(*existing.spans[i], table.render(f, pins[f.field], language))
                for i, f in enumerate(spec.args) if f.field in pins]
    args = [table.render(f, pins[f.field], language) if f.field in pins else table.default(f, language)
            for f in spec.args]
    end = init.spans[-1][1]
    return [Splice(end, end, ", " + table.new(spec.cls, args, language))]
