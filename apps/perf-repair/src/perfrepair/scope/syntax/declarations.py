"""Enclosing method and class, parameters, locals and fields a node declares: declarations in neutral terms."""
from __future__ import annotations

import re

from . import grammar as g
from .node import Node

_PRIVATE = re.compile(r"\bprivate\b")


def enclosing_method(n: Node) -> Node | None:
    for p in (n, *n.ancestors()):
        if p.kind == g.METHOD:
            return p
        if p.type == "block" and p.parent is not None and p.parent.kind == g.CLASS_BODY:
            return p
    return None


def class_chain(n: Node) -> list[Node]:
    return [p for p in n.ancestors() if p.kind == g.CLASS_BODY]


def outermost_class(n: Node) -> Node | None:
    """The outermost class body; the file when the code has no class around it."""
    chain = class_chain(n)
    named = [c for c in chain if c.parent is not None]
    return named[-1] if named else (chain[-1] if chain else None)


def method_name(method: Node | None) -> str | None:
    if method is None or method.type in g.NAMED_ROOTS or method.type == "block":
        return None
    name = method.field("name")
    if name is not None:
        return name.text
    return next((c.text for c in method.children if c.kind == g.IDENTIFIER), None)


def _parameter_name(p: Node) -> str | None:
    if p.type == g.SPREAD_PARAMETER:
        names = [y.text for x in p.children if x.kind == g.DECLARATOR for y in x.children if y.kind == g.IDENTIFIER]
        return names[-1] if names else None
    names = [x for x in p.children if x.kind == g.IDENTIFIER]
    if not names:
        return None
    return (names[0] if p.type == "parameter" else names[-1]).text


def parameters(method: Node | None) -> list[tuple[str, Node]]:
    if method is None:
        return []
    out = []
    for c in method.children:
        if c.type in g.PARAMETER_LISTS:
            for p in c.children:
                if p.type in g.PARAMETERS or p.type == g.SPREAD_PARAMETER:
                    name = _parameter_name(p)
                    if name:
                        out.append((name, p))
    return out


def method_body(method: Node | None) -> Node | None:
    if method is None or method.type == "block":
        return method
    return next((c for c in method.children if c.type in g.BODIES), method)


def is_private(declaration: Node) -> bool:
    return any(c.type == "modifiers" and _PRIVATE.search(c.text) for c in declaration.children)


def declared_names(n: Node) -> list[tuple[str, Node]]:
    """The locals a statement declares, each with its declaring node."""
    if n.kind == g.LOCAL_DECLARATION:
        return [(d.field("name").text, d) for d in n.children if d.kind == g.DECLARATOR and d.field("name")]
    if n.kind != g.PROPERTY_DECLARATION:
        return []
    out = []
    for c in n.children:
        variables = [c] if c.type == g.VARIABLE_DECLARATION else c.children if c.type == g.MULTI_VARIABLE_DECLARATION else []
        for v in variables:
            names = [x for x in v.children if x.kind == g.IDENTIFIER]
            if names:
                out.append((names[0].text, n))
    return out


def declaration_value(declaration: Node) -> Node | None:
    """What a declarator or property declaration initialises to; None when it has no initialiser."""
    if declaration.kind == g.DECLARATOR:
        return declaration.field("value")
    if declaration.kind == g.PROPERTY_DECLARATION and declaration.children:
        last = declaration.children[-1]
        if last.type not in (g.VARIABLE_DECLARATION, g.MULTI_VARIABLE_DECLARATION, "modifiers", "getter", "setter",
                             g.PROPERTY_DELEGATE) and last.type not in g.TYPES:
            return last
    return None


def fields_of(body: Node) -> dict[str, Node]:
    """Fields a class body declares (own, then companion), by name, each with its declaring node."""
    out: dict[str, Node] = {}
    for c in body.children:
        if c.kind == g.FIELD_DECLARATION:
            out.update({d.field("name").text: d for d in c.children if d.kind == g.DECLARATOR and d.field("name")})
        elif c.kind == g.PROPERTY_DECLARATION:
            out.update({name: d for name, d in declared_names(c)})
        elif c.type == g.COMPANION:
            for inner in c.children:
                if inner.kind == g.CLASS_BODY:
                    out.update({k: v for k, v in fields_of(inner).items() if k not in out})
        elif c.type == "enum_body_declarations":
            out.update(fields_of(c))
    out.update({k: v for k, v in _constructor_fields(body).items() if k not in out})
    return out


def class_parameters(body: Node) -> list[Node]:
    owner = body.parent
    if owner is None or owner.type != g.KOTLIN_CLASS:
        return []
    return [q for c in owner.children if c.type == g.PRIMARY_CONSTRUCTOR for q in c.walk() if q.type == g.CLASS_PARAMETER]


def _constructor_fields(body: Node) -> dict[str, Node]:
    out = {}
    for q in class_parameters(body):
        names = [x for x in q.children if x.kind == g.IDENTIFIER]
        if names and re.search(r"\b(val|var)\b", q.text.split(":")[0]):
            out[names[0].text] = q
    return out


def field_owner(declaration: Node) -> Node:
    """The node whose modifiers state the field's visibility."""
    return declaration.parent if declaration.kind == g.DECLARATOR and declaration.parent is not None else declaration


def methods_named(body: Node | None, name: str, arity: int) -> list[Node]:
    if body is None:
        return []
    return [q for q in body.walk() if q.type in ("method_declaration", "function_declaration")
            and method_name(q) == name and len(parameters(q)) == arity]
