"""One method away inside the same class: a field's other methods, a helper's callers, a callee taking the object;
the budget caps how many methods are read, and going over it is recorded, never widened."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..engines import Engines
from ..syntax import grammar as g
from ..syntax.calls import Call, as_call
from ..syntax.declarations import (declaration_value, enclosing_method, is_private, method_body, method_name,
                                   methods_named, outermost_class, parameters)
from ..syntax.resolve import resolve_field, resolve_local
from ..syntax.node import Node
from .binding import bind
from .origins import Source, origin, written_values
from .slice import PASSED, Escape, Slice, scan, scope_calls

# methods read beyond the site's; past it the scope is partially_bounded with `budget`, never a wider reading
METHOD_BUDGET = 6


@dataclass
class Reach:
    """calls: on the object in methods other than the site's; consumers: callees the object is passed to there."""
    calls: list[Call] = field(default_factory=list)
    consumers: list[Call] = field(default_factory=list)
    methods: set[int] = field(default_factory=set)
    over_budget: bool = False

    def admit(self, method: Node | None) -> bool:
        key = id(method)
        if key in self.methods:
            return True
        if len(self.methods) >= METHOD_BUDGET:
            self.over_budget = True
            return False
        self.methods.add(key)
        return True


def same_class_calls(method: Node, at: Node) -> list[Call]:
    name, arity, cls = method_name(method), len(parameters(method)), outermost_class(at)
    if name is None or cls is None:
        return []
    return [c for n in cls.walk() if n.kind == g.CALL and (c := as_call(n)) is not None and c.name == name
            and len(c.args) == arity and (c.receiver is None or c.receiver.kind in (g.THIS, g.SUPER))]


def _bound_calls(at: Node, reach: Reach) -> None:
    """The object a caller receives back from the helper: its chain and, for a local or field, its scanned calls."""
    b = bind(at)
    reach.calls += b.chain + [c for s in b.scope_calls for c in scope_calls(s)]
    if b.kind == "argument" and b.callee is not None:
        reach.consumers.append(b.callee)
    found = resolve_local(b.name, at) if b.kind == "local" and b.name else None
    if found is not None and found.scope is not None:
        s = scan(found.scope, b.name, at.start)
        reach.calls += s.calls
        reach.consumers += [e.call for e in s.escapes if e.kind == PASSED and e.call is not None]
    elif b.kind == "field" and b.name:
        held = resolve_field(b.name, at)
        if held is not None and held.scope is not None:
            reach.calls += scan(held.scope, b.name, held.scope.start).calls


def callers(helper: Node | None, site: Node, reach: Reach) -> None:
    if helper is None:
        return
    for c in same_class_calls(helper, site):
        if c.node.start <= site.start < c.node.end or not reach.admit(enclosing_method(c.node)):
            continue
        _bound_calls(c.node, reach)


def callees(passed: list[Escape], site: Node, reach: Reach) -> None:
    for e in passed:
        reach.consumers.append(e.call)
        if e.call.receiver is not None and e.call.receiver.kind != g.THIS:
            continue
        for target in methods_named(outermost_class(site), e.call.name, len(e.call.args)):
            params = parameters(target)
            if e.index < len(params) and reach.admit(target):
                reach.calls += scan(method_body(target), params[e.index][0], target.start).calls


def field_calls(name: str, site: Node, site_method: Node | None, reach: Reach) -> Slice:
    """Calls on a field across its class; those outside the site's method count against the budget."""
    held = resolve_field(name, site)
    body = held.scope if held is not None else outermost_class(site)
    found = scan(body, name, body.start) if body is not None else Slice()
    for c in found.calls:
        m = enclosing_method(c.node)
        if m is not site_method and reach.admit(m):
            reach.calls.append(c)
    return found


def requirement_depth1(source: Source, at: Node, engines: Engines) -> tuple[str, ...]:
    """A field's written values or a private method's caller arguments, each read back to one origin."""
    if source.origin == "field" and source.field:
        held = resolve_field(source.field, at)
        if held is None or held.scope is None:
            return ()
        initial = declaration_value(held.node)
        values = ([initial] if initial is not None else []) + written_values(source.field, held.scope)
        return tuple(sorted({origin(v, engines, 1).origin for v in values}))
    if source.origin == "parameter" and source.method is not None and is_private(source.method):
        args = [c.args[source.index] for c in same_class_calls(source.method, at) if source.index < len(c.args)]
        return tuple(sorted({origin(a, engines, 1).origin for a in args}))
    return ()
