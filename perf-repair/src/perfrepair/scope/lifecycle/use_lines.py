"""The lines an object with no use found goes on to: references to the name holding it, and the helper's callers in the class."""
from __future__ import annotations

from ...dto.gaps import HELPER_CALLER, OBJECT_REFERENCE
from ...dto.lifecycle import OPEN_ORIGINS
from ..syntax import grammar as g
from ..syntax.declarations import enclosing_method, resolve_field, resolve_local
from ..syntax.node import Node
from .binding import Binding
from .candidates import REACH_HOPS, REACH_LINES, Line, Reached
from .depth1 import same_class_calls

_UNREAD = OPEN_ORIGINS[-1]


def _references(name: str, created: Node) -> list[Node]:
    local, held = resolve_local(name, created), resolve_field(name, created)
    scope = local.scope if local is not None and local.scope is not None else held.scope if held is not None else None
    if scope is None:
        return []
    return [n for n in scope.walk() if n.kind == g.IDENTIFIER and n.text == name and n.line != created.line]


def _callers(created: Node) -> list[Node]:
    """Who calls the method around the object, then who calls those; a helper handing it on."""
    out, seen, frontier = [], set(), [enclosing_method(created)]
    for _ in range(REACH_HOPS):
        calls = [c.node for m in frontier if m is not None for c in same_class_calls(m, created)]
        calls = [c for c in calls if id(c) not in seen]
        seen |= {id(c) for c in calls}
        out += calls
        frontier = [enclosing_method(c) for c in calls]
    return out


def use_lines(created: Node, b: Binding) -> Reached:
    rows = [(OBJECT_REFERENCE, n) for n in _references(b.name, created)] if b.name else []
    rows += [(HELPER_CALLER, n) for n in _callers(created)]
    unique = {n.line: (how, n) for how, n in reversed(rows)}
    lines = [Line(how, line, _UNREAD, n) for line, (how, n) in sorted(unique.items())]
    return Reached(lines[:REACH_LINES], True, len(lines) > REACH_LINES)
