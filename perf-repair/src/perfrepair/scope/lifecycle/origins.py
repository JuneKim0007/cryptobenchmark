"""Where a value comes from, read back through same-method definitions to one origin in the closed list, with its line."""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..engines import Engines
from ..syntax import grammar as g
from ..syntax.calls import as_call
from ..syntax.resolve import (LAMBDA_PARAMETER, LOCAL, PARAMETER, resolve_constructor_parameter, resolve_field,
                              resolve_local)
from ..syntax.declarations import declaration_value, methods_named, outermost_class, parameters
from ..syntax.node import Node
from ..syntax.usage import assignment_sides, refers_to, unwrapped

_DEPTH = 8
_CONSTANT = re.compile(r"[A-Z][A-Z0-9_]+")


@dataclass(frozen=True)
class Source:
    """field: the field's name when origin is field; method, index: the parameter when origin is parameter;
    node: the call of same_class_call, the expression of unknown."""
    origin: str
    line: int
    field: str | None = None
    method: Node | None = None
    index: int | None = None
    node: Node | None = None


def _assigned_values(name: str, scope: Node, before: Node) -> list[Node]:
    out = []
    for n in scope.walk():
        if n.start >= before.start:
            break
        # an assignment that holds `before` (`k = decode(k)`) has not happened yet when its right side reads k
        if n.kind == g.ASSIGNMENT and n.end <= before.start:
            left, right = assignment_sides(n)
            if left is not None and left.kind == g.IDENTIFIER and left.text == name and right is not None:
                out.append(right)
    return out


def _local(name: str, e: Node, found, engines: Engines, depth: int) -> Source:
    if found.kind == PARAMETER:
        params = parameters(found.node)
        return Source(PARAMETER, params[found.index][1].line, method=found.node, index=found.index)
    if found.kind == LAMBDA_PARAMETER:
        return Source(PARAMETER, found.node.line)
    initial = declaration_value(found.node) if found.node.kind in (g.DECLARATOR, g.PROPERTY_DECLARATION) else None
    values = [v for v in ([initial] if initial is not None else []) + _assigned_values(name, found.scope, e)
              if v.text != "null"]
    return origin(values[-1], engines, depth + 1) if values else Source("unknown", e.line)


def _identifier(e: Node, engines: Engines, depth: int) -> Source:
    name = e.text
    found = resolve_local(name, e)
    if found is not None and found.kind in (LOCAL, PARAMETER, LAMBDA_PARAMETER):
        return _local(name, e, found, engines, depth)
    held = resolve_field(name, e)
    if held is not None:
        return Source("field", held.node.line, field=name)
    if resolve_constructor_parameter(name, e) is not None:
        return Source(PARAMETER, e.line)
    return Source("field" if _CONSTANT.fullmatch(name) else "unknown", e.line, field=name if _CONSTANT.fullmatch(name) else None)


def _member(e: Node, engines: Engines, depth: int) -> Source:
    first, last = e.children[0], e.children[-1].text
    if first.kind == g.THIS:
        return Source("field", e.line, field=last)
    if last in engines.accessors:
        return origin(first, engines, depth + 1)
    return Source("field" if _CONSTANT.fullmatch(last) else "other_call", e.line)


def _call(e: Node, engines: Engines, depth: int) -> Source:
    c = as_call(e)
    named = engines.origin_of_call(c.name)
    if named is not None and (c.receiver is not None or named in ("generated", "derived", "literal")):
        return Source(named, e.line)
    if c.name in engines.specs and (e.kind == g.NEW or c.receiver is None):
        index = engines.specs[c.name]
        return origin(c.args[min(index, len(c.args) - 1)], engines, depth + 1) if c.args else Source("unknown", e.line)
    if c.name in engines.accessors and c.receiver is not None:
        return origin(c.receiver, engines, depth + 1)
    if c.name in engines.decoders and c.args:
        return origin(c.args[0], engines, depth + 1)
    if e.kind != g.NEW and (c.receiver is None or c.receiver.kind == g.THIS) \
            and methods_named(outermost_class(e), c.name, len(c.args)):
        return Source("same_class_call", e.line, node=e)
    return Source("other_call", e.line)


def origin(e: Node | None, engines: Engines, depth: int = 0) -> Source:
    e = unwrapped(e)
    if e is None or depth > _DEPTH:
        return Source("unknown", e.line if e is not None else 0)
    if e.kind == g.CAST:
        value = next((c for c in e.children if c.type not in g.TYPES), None)
        return origin(value, engines, depth + 1)
    if e.kind in (g.LITERAL, g.ARRAY_LITERAL) or e.kind == g.ARRAY_NEW and any(c.kind == g.ARRAY_LITERAL for c in e.children):
        return Source("literal", e.line)
    if e.kind == g.IDENTIFIER:
        return _identifier(e, engines, depth)
    if e.kind == g.MEMBER and e.children:
        return _member(e, engines, depth)
    if e.kind in (g.CALL, g.NEW) and as_call(e) is not None:
        return _call(e, engines, depth)
    return Source("unknown", e.line, node=e)


def written_values(name: str, body: Node) -> list[Node]:
    """A field's initializer and every value the class assigns to it."""
    out = []
    for n in body.walk():
        if n.kind == g.ASSIGNMENT:
            left, right = assignment_sides(n)
            if left is not None and right is not None and refers_to(left, name) and right.text != "null":
                out.append(right)
    return out
