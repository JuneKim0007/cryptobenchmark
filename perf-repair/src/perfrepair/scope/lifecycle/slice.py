"""Calls on one named object inside one scope, from a point on, stopping where a nested declaration shadows the name;
and where the object escapes: returned, passed, stored, aliased."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..syntax import grammar as g
from ..syntax.calls import Call, as_call, lambda_parameter
from ..syntax.declarations import declared_names, parameters
from ..syntax.node import Node
from ..syntax.usage import ARGUMENT, ASSIGNED, DECLARED, RECEIVER, RETURNED, refers_to, use_of

RETURN, PASSED, STORED, ALIAS = "return", "argument", "store", "alias"


@dataclass(frozen=True)
class Escape:
    kind: str
    node: Node
    call: Call | None = None
    index: int | None = None
    name: str | None = None


@dataclass
class Slice:
    calls: list[Call] = field(default_factory=list)
    escapes: list[Escape] = field(default_factory=list)

    def extend(self, other: "Slice") -> None:
        self.calls += other.calls
        self.escapes += other.escapes


def scope_calls(call: Call) -> list[Call]:
    """The calls a scope function's lambda makes on the object: unqualified for an implicit receiver, else on `it`."""
    if call.lambda_ is None:
        return []
    implicit, name = call.name in g.IMPLICIT_RECEIVER, lambda_parameter(call.lambda_)
    out = []
    for n in call.lambda_.walk():
        inner = as_call(n) if n.kind == g.CALL else None
        if inner is None or inner is call:
            continue
        if implicit and inner.receiver is None or not implicit and inner.receiver is not None and refers_to(inner.receiver, name):
            out.append(inner)
    return out


def _shadows(n: Node, name: str) -> bool:
    if n.kind == g.METHOD:
        return name in [p for p, _ in parameters(n)]
    if n.kind == g.LAMBDA and n.type != g.ANNOTATED_LAMBDA:
        params = [x for x in n.children if x.type == g.LAMBDA_PARAMETERS] or ([n.field("parameters")] if n.field("parameters") else [])
        return any(x.kind == g.IDENTIFIER and x.text == name for p in params for x in p.walk())
    return False


def _escape(n: Node) -> Escape | None:
    use = use_of(n)
    if use.kind == RETURNED:
        return Escape(RETURN, use.node or n)
    if use.kind == ARGUMENT and use.call is not None:
        return Escape(PASSED, use.call.node, use.call, use.index)
    if use.kind == ASSIGNED:
        return Escape(STORED, use.node, name=use.target.text if use.target is not None else None)
    if use.kind == DECLARED:
        return Escape(ALIAS, use.node, name=use.name)
    return None


def _on_object(n: Node, name: str, out: Slice) -> None:
    use = use_of(n)
    if use.kind == RECEIVER and use.call is not None:
        call = use.call
        out.calls += scope_calls(call) if call.name in g.SCOPE_FUNCTIONS else [call]
        return
    if use.kind == ARGUMENT and use.call is not None and use.call.receiver is None and use.call.name in g.IMPLICIT_RECEIVER \
            and use.index == 0:
        out.calls += scope_calls(use.call)
        return
    escape = _escape(n)
    if escape is not None:
        out.escapes.append(escape)


def scan(scope: Node, name: str, start: int) -> Slice:
    """Every reference to `name` at or after byte `start` in `scope`, read as a call on it or an escape."""
    out, stack = Slice(), [scope]
    while stack:
        n = stack.pop()
        if n.end <= start or (n is not scope and _shadows(n, name)):
            continue
        if n.kind in (g.BLOCK, g.FUNCTION_BODY) or n.type == g.LAMBDA_LITERAL:
            redeclared = next((s for s in n.children if s.start > start and any(d == name for d, _ in declared_names(s))),
                              None)
            stack.extend(reversed([c for c in n.children if redeclared is None or c.start < redeclared.start]))
            continue
        if n.start >= start and refers_to(n, name) and n.kind in (g.IDENTIFIER, g.MEMBER):
            _on_object(n, name, out)
            if n.kind == g.MEMBER:
                continue
        stack.extend(reversed(n.children))
    return out
