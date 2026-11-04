"""What a name resolves to at a point: the nearest local or parameter, an enclosing class's field, a constructor parameter."""
from __future__ import annotations

from dataclasses import dataclass

from . import grammar as g
from .declarations import (
    class_chain,
    class_parameters,
    declared_names,
    fields_of,
    parameters,
)
from .node import Node

LOCAL, PARAMETER, LAMBDA_PARAMETER, FIELD, CONSTRUCTOR_PARAMETER = (
    "local", "parameter", "lambda_parameter", "field", "constructor_parameter")


@dataclass(frozen=True)
class Resolved:
    """kind: LOCAL (node its declaration, scope the block holding it), PARAMETER (node its method, index its position),
    LAMBDA_PARAMETER, FIELD (node its declaration, scope the class body), CONSTRUCTOR_PARAMETER."""
    kind: str
    node: Node
    scope: Node | None = None
    statement: Node | None = None
    index: int = 0


def _local_in_block(name: str, child: Node, block: Node) -> Resolved | None:
    found = None
    for statement in block.children:
        if statement.start >= child.end:
            break
        if statement.start >= child.start and not (statement.kind in (g.LOCAL_DECLARATION, g.PROPERTY_DECLARATION)
                                                   and statement.start <= child.start < statement.end):
            break
        for declared, node in declared_names(statement):
            if declared == name:
                found = Resolved(LOCAL, node, block, statement)
    return found


def _binding_in_scope(name: str, child: Node, scope: Node) -> Resolved | None:
    for c in scope.walk():
        if c.start >= child.start:
            break
        if c.type in g.BINDING_NODES and any(x.kind == g.IDENTIFIER and x.text == name for x in c.children):
            if scope.kind == g.LAMBDA:
                return Resolved(LAMBDA_PARAMETER, scope)
            return Resolved(LOCAL, c, scope, c)
    if scope.type == g.LAMBDA_EXPRESSION:
        p = scope.field("parameters")
        if p is not None and p.kind == g.IDENTIFIER and p.text == name:
            return Resolved(LAMBDA_PARAMETER, scope)
    return None


def resolve_local(name: str, at: Node) -> Resolved | None:
    """The nearest local or parameter visible at `at`; stops at the class boundary."""
    child, p = at, at.parent
    while p is not None and p.kind != g.CLASS_BODY:
        found = None
        if p.kind == g.BLOCK or p.kind == g.FUNCTION_BODY or p.type in ("switch_block_statement_group", g.LAMBDA_LITERAL):
            found = _local_in_block(name, child, p)
        if found is None and p.type in g.BINDING_SCOPES:
            found = _binding_in_scope(name, child, p)
        if found is None and p.kind == g.METHOD:
            names = [n for n, _ in parameters(p)]
            if name in names:
                found = Resolved(PARAMETER, p, index=names.index(name))
        if found is not None:
            return found
        child, p = p, p.parent
    return None


def resolve_field(name: str, at: Node) -> Resolved | None:
    for body in class_chain(at):
        declared = fields_of(body)
        if name in declared:
            return Resolved(FIELD, declared[name], body)
    return None


def resolve_constructor_parameter(name: str, at: Node) -> Node | None:
    for body in class_chain(at):
        for q in class_parameters(body):
            names = [x for x in q.children if x.kind == g.IDENTIFIER]
            if names and names[0].text == name:
                return q
    return None
