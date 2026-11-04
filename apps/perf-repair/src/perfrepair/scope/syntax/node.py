"""A parsed node as plain data: its neutral kind, position, parent, named children; no parser object survives parsing."""
from __future__ import annotations

from typing import Iterator


class Node:
    __slots__ = ("type", "kind", "start", "end", "line", "end_line", "parent", "has_error", "children", "fields", "_source")

    def __init__(self, type_: str, kind: str, start: int, end: int, line: int, end_line: int, parent: "Node | None",
                 has_error: bool, source: bytes):
        self.type, self.kind, self.start, self.end = type_, kind, start, end
        self.line, self.end_line, self.parent, self.has_error = line, end_line, parent, has_error
        self.children: list[Node] = []
        self.fields: dict[str, Node] = {}
        self._source = source

    @property
    def text(self) -> str:
        return self._source[self.start:self.end].decode("utf8", "replace")

    def field(self, name: str) -> "Node | None":
        return self.fields.get(name)

    def walk(self) -> Iterator["Node"]:
        """This node and its descendants in source order."""
        stack = [self]
        while stack:
            n = stack.pop()
            yield n
            stack.extend(reversed(n.children))

    def ancestors(self) -> Iterator["Node"]:
        p = self.parent
        while p is not None:
            yield p
            p = p.parent
