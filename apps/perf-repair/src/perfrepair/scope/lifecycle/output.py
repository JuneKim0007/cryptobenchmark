"""Whether a site's output stays in its function: read only by comparisons of its own outputs. A reference from
elsewhere was made by the current algorithm, so a swap breaks that comparison and it does not count."""
from __future__ import annotations

from collections.abc import Collection

from ..syntax import grammar as g
from ..syntax.calls import Call
from ..syntax.node import Node
from ..syntax.usage import ARGUMENT, DECLARED, RECEIVER, unwrapped, use_of


def _operands(call: Call) -> list[Node | None]:
    """`Arrays.equals(a, b)` holds both in its arguments, `a.equals(b)` one in its receiver."""
    return list(call.args) if len(call.args) == 2 else [call.receiver, *call.args]


def compared_only(terminals: list[Call], body: Node | None, comparisons: Collection[str]) -> bool:
    uses = [use_of(c.node) for c in terminals]
    held = {u.name for u in uses if u.kind == DECLARED and not u.is_field}
    # a declaration's own name, before its value, is not a read of the value
    spans = [(u.declaration.start, c.node.start) for c, u in zip(terminals, uses) if u.kind == DECLARED]

    def own(n: Node | None) -> bool:
        n = unwrapped(n)
        return n is not None and (any(n is c.node for c in terminals) or (n.kind == g.IDENTIFIER and n.text in held))

    def compares(n: Node) -> bool:
        use = use_of(n)
        return (use.kind in (ARGUMENT, RECEIVER) and use.call is not None and use.call.name in comparisons
                and all(own(x) for x in _operands(use.call)))

    if len(terminals) < 2 or body is None or any(u.kind == DECLARED and u.is_field for u in uses):
        return False
    reads = [c.node for c, u in zip(terminals, uses) if u.kind != DECLARED]
    reads += [n for n in body.walk() if n.kind == g.IDENTIFIER and n.text in held
              and not any(start <= n.start and n.end <= end for start, end in spans)]
    return all(compares(n) for n in reads)
