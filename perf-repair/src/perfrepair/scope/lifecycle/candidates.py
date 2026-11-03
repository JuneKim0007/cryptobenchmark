"""The lines code can reach for one open value: a field's writes, a parameter's in-class call arguments, a same-class
call's returned values, an expression's parts; read on from each open one, within a budget it never widens."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from ...dto.gaps import CALLER_ARGUMENT, FIELD_WRITE, PART, RETURNED
from ...dto.lifecycle import OPEN_ORIGINS
from ..engines import Engines
from ..syntax import grammar as g
from ..syntax.calls import as_call
from ..syntax.declarations import (declaration_value, enclosing_method, field_owner, is_private, method_body,
                                   methods_named, outermost_class, resolve_field)
from ..syntax.node import Node
from ..syntax.usage import unwrapped
from .depth1 import same_class_calls
from .origins import Source, origin, written_values

# per gap: methods read past the site's, hops from the value, lines offered; past one it is recorded, never widened
REACH_METHODS, REACH_HOPS, REACH_LINES = 12, 3, 8
_VALUE_KINDS = (g.IDENTIFIER, g.MEMBER, g.CALL, g.NEW, g.LITERAL)


@dataclass(frozen=True)
class Line:
    how: str
    line: int
    reads: str
    node: Node | None = None


@dataclass
class Reached:
    """lines: in the order reached; open_ends: an open reading nothing further closes; over_budget: reading stopped early."""
    lines: list[Line] = field(default_factory=list)
    open_ends: bool = False
    over_budget: bool = False

    @property
    def settled(self) -> Line | None:
        """Every closed line reads one origin, and no path stayed open or was cut."""
        closed = {x.reads for x in self.lines if x.reads not in OPEN_ORIGINS}
        if len(closed) == 1 and not self.open_ends and not self.over_budget:
            return next(x for x in self.lines if x.reads in closed)
        return None


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
    # only branches and joins carry their operands' value: an array's size or an index does not
    if e is None or e.kind != g.FLOW:
        return []
    out = []
    for c in e.children:
        inner = unwrapped(c)
        if inner is not None:
            out += [inner] if inner.kind in _VALUE_KINDS else _parts(inner)
    return out


def _next_values(src: Source, at: Node) -> list[tuple[str, Node]]:
    if src.origin == "field":
        return [(FIELD_WRITE, v) for v in _field_values(src, at)]
    if src.origin == "parameter":
        return [(CALLER_ARGUMENT, v) for v in _caller_values(src, at)]
    if src.origin == "same_class_call":
        return [(RETURNED, v) for v in _called_values(src)]
    return [(PART, v) for v in _parts(src.node)] if src.origin == "unknown" else []


def _outside_writers(src: Source, at: Node) -> bool:
    """Other classes can pass or write this value too, so the lines in the class cannot close it."""
    if src.origin == "parameter":
        return src.method is None or not is_private(src.method)
    held = resolve_field(src.field, at) if src.origin == "field" and src.field else None
    return held is not None and not is_private(field_owner(held.node))


def _line(how: str, value: Node, src: Source) -> Line:
    # a closed reading names where the value is made; an open one where this path hands it on
    return Line(how, value.line if src.origin in OPEN_ORIGINS else src.line, src.origin, value)


def _follow(src: Source, node: Node, hops: int, out: Reached, methods: set[int]) -> list[tuple[str, Node, int]]:
    """The next values to read from an open one; a path that ends open or over budget is recorded on `out`."""
    following = _next_values(src, node)
    out.open_ends = out.open_ends or _outside_writers(src, node) or not following
    methods |= {id(enclosing_method(v)) for _, v in following}
    if following and (hops >= REACH_HOPS or len(methods) > REACH_METHODS):
        out.over_budget = True
        return []
    return [(h, v, hops + 1) for h, v in following]


def reach(value: Node, engines: Engines) -> Reached:
    """Breadth first from the requirement's own argument, so the nearest lines are the ones a budget keeps."""
    out, seen, methods = Reached(), set(), set()
    queue = deque([("", value, 0)])
    while queue:
        how, node, hops = queue.popleft()
        if id(node) in seen:
            continue
        seen.add(id(node))
        src = origin(node, engines)
        if how and len(out.lines) >= REACH_LINES:
            out.over_budget = True
            break
        if how:
            out.lines.append(_line(how, node, src))
        if src.origin in OPEN_ORIGINS:
            queue.extend(_follow(src, node, hops, out, methods))
    return out
