"""Code settlement: an open requirement whose every path, inside its class, closes to one origin is stored and never asked.
A path follows field writes, in-class call arguments, returned values and a branch's operands; a budget never widens it."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field, replace

from ...dto.lifecycle import OPEN_ORIGINS, Lifecycle, Requirement, Settled
from ..engines import Engines
from ..syntax import grammar as g
from ..syntax.calls import as_call
from ..syntax.declarations import (declaration_value, enclosing_method, field_owner, is_private, method_body,
                                   methods_named, outermost_class)
from ..syntax.resolve import resolve_field
from ..syntax.node import Node
from ..syntax.usage import unwrapped
from .depth1 import same_class_calls
from .origins import Source, origin, written_values
from .read import Reading

# per requirement: methods read past the site's, hops from the value, values read; past one it stays open
REACH_METHODS, REACH_HOPS, REACH_LINES = 12, 3, 8
_VALUE_KINDS = (g.IDENTIFIER, g.MEMBER, g.CALL, g.NEW, g.LITERAL)


@dataclass
class _Walk:
    """read: values read past the requirement's own argument; closed: those closing; unsettled: a path stayed open or was cut."""
    read: int = 0
    closed: list[Source] = field(default_factory=list)
    unsettled: bool = False
    methods: set[int] = field(default_factory=set)


def _field_values(src: Source, at: Node) -> list[Node]:
    held = resolve_field(src.field, at) if src.field else None
    if held is None or held.scope is None:
        return []
    initial = declaration_value(held.node)
    return ([initial] if initial is not None else []) + written_values(src.field, held.scope)


def _caller_values(src: Source, at: Node) -> list[Node]:
    if src.method is None or src.index is None:
        return []
    return [c.args[src.index] for c in same_class_calls(src.method, at) if src.index < len(c.args)]


def _is_expression_body(body: Node) -> bool:
    return body.kind == g.FUNCTION_BODY and not any(c.kind == g.BLOCK for c in body.children)


def _returned(method: Node) -> list[Node]:
    body = method_body(method)
    if body is None:
        return []
    if _is_expression_body(body):
        return [c for c in body.children if c.type not in g.COMMENTS][-1:]
    returns = (n for n in body.walk() if n.kind == g.RETURN and n.children)
    return [n.children[-1] for n in returns if enclosing_method(n) is method]


def _called_values(src: Source) -> list[Node]:
    call = as_call(src.node) if src.node is not None else None
    if call is None:
        return []
    return [v for m in methods_named(outermost_class(src.node), call.name, len(call.args)) for v in _returned(m)]


def _parts(e: Node | None) -> list[Node]:
    # only a branch hands on one operand's value: a join, an array's size or an index does not
    if e is None or e.kind != g.FLOW or e.type in g.JOINS:
        return []
    out = []
    for c in e.children:
        inner = unwrapped(c)
        if inner is not None:
            out += [inner] if inner.kind in _VALUE_KINDS else _parts(inner)
    return out


def _next_values(src: Source, at: Node) -> list[Node]:
    if src.origin == "field":
        return _field_values(src, at)
    if src.origin == "parameter":
        return _caller_values(src, at)
    if src.origin == "same_class_call":
        return _called_values(src)
    return _parts(src.node) if src.origin == "unknown" else []


def _outside_writers(src: Source, at: Node) -> bool:
    """Other classes can pass or write this value too, so the lines in the class cannot close it."""
    if src.origin == "parameter":
        return src.method is None or not is_private(src.method)
    held = resolve_field(src.field, at) if src.origin == "field" and src.field else None
    return held is not None and not is_private(field_owner(held.node))


def _follow(src: Source, node: Node, hops: int, walk: _Walk) -> list[tuple[Node, int]]:
    following = _next_values(src, node)
    walk.methods |= {id(enclosing_method(v)) for v in following}
    cut = following and (hops >= REACH_HOPS or len(walk.methods) > REACH_METHODS)
    if cut or not following or _outside_writers(src, node):
        walk.unsettled = True
    return [(v, hops + 1) for v in following]


def _closing_source(value: Node, engines: Engines) -> Source | None:
    """Breadth first from the requirement's own argument; the first closing value is the line stored."""
    walk, seen = _Walk(), set()
    queue = deque([(value, 0)])
    while queue and not walk.unsettled:
        node, hops = queue.popleft()
        if id(node) in seen:
            continue
        seen.add(id(node))
        src = origin(node, engines)
        walk.read += 1 if hops else 0
        walk.unsettled = walk.read > REACH_LINES
        if src.origin in OPEN_ORIGINS:
            queue.extend(_follow(src, node, hops, walk))
        elif hops:
            walk.closed.append(src)
    one = len({s.origin for s in walk.closed}) == 1 and not walk.unsettled
    return walk.closed[0] if one else None


def _settled(r: Requirement, value: Node, engines: Engines) -> Requirement:
    src = _closing_source(value, engines)
    return replace(r, settled=Settled(src.origin, src.line)) if src is not None else r


def settle(reading: Reading, engines: Engines) -> Lifecycle:
    lc = reading.lifecycle
    return replace(lc, requirements=tuple(_settled(r, reading.values[r], engines) if r.open else r for r in lc.requirements))
