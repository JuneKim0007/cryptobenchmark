"""A call in neutral terms: its receiver, name, arguments and trailing lambda; finding one by line."""
from __future__ import annotations

import re
from dataclasses import dataclass

from . import grammar as g
from .node import Node


@dataclass(frozen=True)
class Call:
    node: Node
    receiver: Node | None
    name: str
    args: tuple[Node, ...]
    lambda_: Node | None
    named_at: Node | None = None

    @property
    def line(self) -> int:
        """The line of the call's name: a chained call starts where its receiver does."""
        return (self.named_at or self.node).line


def _java_call(n: Node) -> Call:
    arguments, name = n.field("arguments"), n.field("name")
    return Call(n, n.field("object"), name.text if name else "", tuple(arguments.children) if arguments else (), None, name)


def _new_call(n: Node) -> Call:
    type_, arguments = n.field("type"), n.field("arguments")
    name = type_.text.split("<")[0].split(".")[-1] if type_ else ""
    return Call(n, None, name, tuple(arguments.children) if arguments else (), None)


def _kotlin_call(n: Node) -> Call | None:
    if not n.children:
        return None
    function, args, trailing = n.children[0], [], None
    for c in n.children[1:]:
        if c.kind == g.ARGUMENTS:
            args += [v.children[-1] for v in c.children if v.kind == g.ARGUMENT and v.children]
        elif c.type == g.ANNOTATED_LAMBDA:
            trailing = c
    outer = n.parent
    if trailing is None and outer is not None and outer.kind == g.CALL and outer.children and outer.children[0] is n:
        # `f(x) { ... }` parses as a call of the call `f(x)` with the lambda; the lambda is f's
        trailing = next((c for c in outer.children if c.type == g.ANNOTATED_LAMBDA), None)
    if function.kind == g.MEMBER and function.children:
        return Call(n, function.children[0], function.children[-1].text, tuple(args), trailing, function.children[-1])
    return Call(n, None, function.text, tuple(args), trailing) if function.kind == g.IDENTIFIER else None


def as_call(n: Node) -> Call | None:
    if n.kind == g.NEW:
        return _new_call(n)
    if n.kind != g.CALL:
        return None
    return _java_call(n) if "name" in n.fields else _kotlin_call(n)


def lambda_owner(annotated: Node) -> Call | None:
    """The call a trailing lambda belongs to."""
    owner = annotated.parent
    if owner is None or owner.kind != g.CALL:
        return None
    return as_call(owner) or (as_call(owner.children[0]) if owner.children and owner.children[0].kind == g.CALL else None)


def _squeezed(text: str) -> str:
    return re.sub(r"\s+", "", text)


def find_call(root: Node, line: int, text: str, factories: frozenset[str], engine: str) -> Node | None:
    """The factory call the scan recorded at `line`: same text first, then the engine's receiver, then what starts there."""
    found = [(n, c) for n in root.walk() if n.line <= line <= n.end_line and n.kind == g.CALL
             and (c := as_call(n)) is not None and c.name in factories]
    if not found:
        return None
    want = _squeezed(text)
    same = [n for n, _ in found if _squeezed(n.text) == want]
    if same:
        return same[0]
    typed = [n for n, c in found if c.receiver is not None and c.receiver.text.split(".")[-1] == engine]
    if typed:
        return typed[0]
    starting = [n for n, _ in found if n.line == line]
    return starting[0] if starting else None


def lambda_parameter(lambda_: Node) -> str:
    """The name the lambda's single value goes by; `it` when it declares none."""
    for n in lambda_.walk():
        if n.type == g.LAMBDA_PARAMETERS:
            names = [x.text for x in n.walk() if x.kind == g.IDENTIFIER]
            if names:
                return names[0]
    return "it"
