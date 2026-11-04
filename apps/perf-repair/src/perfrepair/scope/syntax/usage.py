"""What the code around an expression does with its value: receiver, argument, declaration, assignment, return, or nothing."""
from __future__ import annotations

from dataclasses import dataclass

from . import grammar as g
from .calls import Call, as_call, lambda_owner
from .declarations import declared_names
from .node import Node

RECEIVER, MEMBER_READ, ARGUMENT, DECLARED, ASSIGNED, RETURNED, DISCARDED, LAMBDA_VALUE, CONTAINER, NOT_A_VALUE, UNKNOWN = (
    "receiver", "member_read", "argument", "declared", "assigned", "returned", "discarded", "lambda_value", "container",
    "not_a_value", "unknown")
_LIMIT = 40


@dataclass(frozen=True)
class Use:
    kind: str
    call: Call | None = None
    index: int | None = None
    name: str | None = None
    declaration: Node | None = None
    is_field: bool = False
    target: Node | None = None
    node: Node | None = None


def unwrapped(n: Node | None) -> Node | None:
    while n is not None and n.kind == g.WRAPPING and len(n.children) == 1:
        n = n.children[0]
    return n


def refers_to(n: Node, name: str) -> bool:
    """`n` is the plain name or `this.name`."""
    n = unwrapped(n)
    if n is None:
        return False
    if n.kind == g.IDENTIFIER:
        return n.text == name
    return n.kind == g.MEMBER and len(n.children) == 2 and n.children[0].kind == g.THIS and n.children[1].text == name


def assignment_sides(a: Node) -> tuple[Node | None, Node | None]:
    if a.field("left") is not None:
        return a.field("left"), a.field("right")
    return (a.children[0], a.children[-1]) if a.children else (None, None)


def _member_use(n: Node, p: Node) -> Use | None:
    if p.children[0] is not n:
        return Use(NOT_A_VALUE)
    outer = p.parent
    if outer is not None and outer.kind == g.CALL and outer.children and outer.children[0] is p:
        return Use(RECEIVER, as_call(outer), node=outer)
    return Use(MEMBER_READ, node=p)


def _java_call_use(n: Node, p: Node) -> Use | None:
    if p.field("object") is n:
        return Use(RECEIVER, as_call(p), node=p)
    return Use(NOT_A_VALUE)


def _argument_use(n: Node, p: Node) -> Use:
    list_ = p if p.kind == g.ARGUMENTS else p.parent
    owner = list_.parent if list_ is not None else None
    call = as_call(owner) if owner is not None else None
    if call is None:
        return Use(UNKNOWN)
    index = next((i for i, a in enumerate(call.args) if a is n), None)
    return Use(ARGUMENT, call, index) if index is not None else Use(NOT_A_VALUE)


def _field_like(declaration: Node) -> bool:
    return declaration.parent is not None and (declaration.parent.kind == g.CLASS_BODY or declaration.parent.type == "enum_body_declarations")


def _declared_use(n: Node, p: Node) -> Use:
    if p.kind == g.DECLARATOR:
        if p.field("value") is not n:
            return Use(NOT_A_VALUE)
        owner = p.parent
        return Use(DECLARED, name=p.field("name").text, declaration=p, is_field=owner.kind == g.FIELD_DECLARATION, node=owner)
    declaration = p if p.kind == g.PROPERTY_DECLARATION else p.parent
    if declaration is None:
        return Use(UNKNOWN)
    names = declared_names(declaration)
    if not names:
        return Use(CONTAINER) if p.kind == g.PROPERTY_DECLARATION and p.children[-1] is n else Use(NOT_A_VALUE)
    if p.kind == g.PROPERTY_DECLARATION and p.children[-1] is not n:
        return Use(NOT_A_VALUE)
    return Use(DECLARED, name=names[0][0], declaration=declaration, is_field=_field_like(declaration), node=declaration)


def _block_use(n: Node, p: Node) -> Use | None:
    if p.children and p.children[-1] is not n:
        return Use(DISCARDED)
    owner = p.parent
    if p.type == g.LAMBDA_LITERAL:
        holder = p.parent
        call = lambda_owner(holder) if holder is not None and holder.type == g.ANNOTATED_LAMBDA else None
        if call is not None and call.name in g.VALUE_CALLS:
            return Use("through", node=holder.parent)
        return Use(LAMBDA_VALUE)
    if owner is not None and (owner.kind in (g.METHOD, g.FUNCTION_BODY) or owner.kind == g.CLASS_BODY):
        return Use(DISCARDED)
    return Use("through", node=p)


def _one_step(n: Node) -> Use:
    p = n.parent
    if p is None:
        return Use(UNKNOWN)
    kind = p.kind
    if kind == g.MEMBER:
        return _member_use(n, p)
    if kind == g.CALL:
        if "name" in p.fields:
            return _java_call_use(n, p)
        return Use(NOT_A_VALUE)
    if kind in (g.ARGUMENTS, g.ARGUMENT):
        return _argument_use(n, p)
    if kind in (g.DECLARATOR, g.PROPERTY_DECLARATION, g.PROPERTY_DELEGATE):
        return _declared_use(n, p)
    if kind == g.ASSIGNMENT:
        left, right = assignment_sides(p)
        return Use(ASSIGNED, target=left, node=p) if right is n else Use(NOT_A_VALUE)
    if kind == g.RETURN:
        return Use(RETURNED, node=p)
    if kind == g.FUNCTION_BODY:
        return Use(RETURNED, node=p)
    if kind == g.EXPRESSION_STATEMENT:
        return Use(DISCARDED)
    if p.type == g.LAMBDA_EXPRESSION:
        return Use(LAMBDA_VALUE)
    if kind in (g.BLOCK,) or p.type == g.LAMBDA_LITERAL:
        return _block_use(n, p)
    if kind in (g.WRAPPING, g.CAST, g.FLOW):
        return Use("through", node=p)
    if kind in (g.ARRAY_LITERAL, g.ARRAY_NEW, g.CONTAINER):
        return Use(CONTAINER)
    return Use(UNKNOWN)


def use_of(n: Node) -> Use:
    """Follows the value out through parentheses, casts and branches to what finally receives it."""
    for _ in range(_LIMIT):
        step = _one_step(n)
        if step.kind != "through":
            return step
        n = step.node
    return Use(UNKNOWN)


def _runs_later(p: Node) -> bool:
    if p.kind == g.METHOD or p.type == g.LAMBDA_EXPRESSION:
        return True
    if p.type == g.LAMBDA_LITERAL and (p.parent is None or p.parent.type != g.ANNOTATED_LAMBDA):
        return True
    if p.type == g.ANNOTATED_LAMBDA:
        owner = lambda_owner(p)
        return owner is None or owner.name not in g.INLINE_CALLS
    return False


def executable_root(n: Node) -> Node | None:
    """The method or non-inline lambda that runs `n`."""
    return next((p for p in n.ancestors() if _runs_later(p)), None)
