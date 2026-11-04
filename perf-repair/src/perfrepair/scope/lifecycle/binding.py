"""Where the created object goes first: a chain of calls, a local, a field, a return, an argument, or nowhere."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..syntax import grammar as g
from ..syntax.calls import Call
from ..syntax.resolve import LOCAL, PARAMETER, resolve_local
from ..syntax.node import Node
from ..syntax.usage import ARGUMENT, ASSIGNED, DECLARED, DISCARDED, MEMBER_READ, RECEIVER, RETURNED, use_of

_LIMIT = 40


@dataclass
class Binding:
    """chain: calls made on the object before it is bound; scope_calls: scope-function calls whose lambda acts on it."""
    kind: str
    name: str | None = None
    declaration: Node | None = None
    callee: Call | None = None
    index: int | None = None
    chain: list[Call] = field(default_factory=list)
    scope_calls: list[Call] = field(default_factory=list)


def _assigned(target: Node | None, at: Node, b: Binding) -> Binding:
    if target is None:
        return Binding("other", chain=b.chain, scope_calls=b.scope_calls)
    if target.kind == g.IDENTIFIER:
        found = resolve_local(target.text, at)
        if found is not None and found.kind in (LOCAL, PARAMETER):
            return Binding("local", target.text, found.node, chain=b.chain, scope_calls=b.scope_calls)
        return Binding("field", target.text, chain=b.chain, scope_calls=b.scope_calls)
    if target.kind == g.MEMBER and len(target.children) == 2 and target.children[0].kind == g.THIS:
        return Binding("field", target.children[1].text, chain=b.chain, scope_calls=b.scope_calls)
    return Binding("other", target.text, chain=b.chain, scope_calls=b.scope_calls)


def _final(use, b: Binding) -> Binding:
    if use.kind == DECLARED:
        return Binding("field" if use.is_field else "local", use.name, use.declaration, chain=b.chain,
                       scope_calls=b.scope_calls)
    if use.kind == ASSIGNED:
        return _assigned(use.target, use.node, b)
    if use.kind == RETURNED:
        return Binding("returned", chain=b.chain, scope_calls=b.scope_calls)
    if use.kind == ARGUMENT and use.index == 0 and use.call.receiver is None and use.call.name in g.SCOPE_FUNCTIONS:
        return Binding("chain", chain=b.chain, scope_calls=[*b.scope_calls, use.call])
    if use.kind == ARGUMENT:
        return Binding("argument", callee=use.call, index=use.index, chain=b.chain, scope_calls=b.scope_calls)
    if use.kind in (DISCARDED, MEMBER_READ):
        return Binding("chain" if b.chain or b.scope_calls or use.kind == MEMBER_READ else "discarded", chain=b.chain,
                       scope_calls=b.scope_calls)
    return Binding("other", chain=b.chain, scope_calls=b.scope_calls)


def bind(created: Node) -> Binding:
    """Follows the value through scope functions that hand the object on, to what finally holds it."""
    b, n = Binding("other"), created
    for _ in range(_LIMIT):
        use = use_of(n)
        if use.kind != RECEIVER or use.call is None:
            return _final(use, b)
        call = use.call
        if call.name not in g.SCOPE_FUNCTIONS:
            b.chain.append(call)
            return Binding("chain", chain=b.chain, scope_calls=b.scope_calls)
        b.scope_calls.append(call)
        if call.name not in g.RETURNS_RECEIVER:
            return Binding("chain", chain=b.chain, scope_calls=b.scope_calls)
        n = use.node
    return b
