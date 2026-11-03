"""What links need from a scope's file beyond its lifecycle: the class around it, the type its method returns, the
types of the parameters on a line, and the file's lines."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from ...dto.lifecycle import Requirement
from ...dto.site import Scope
from ...source.language import of_file
from ..engines import read_engines
from ..syntax import grammar as g
from ..syntax.calls import find_call
from ..syntax.declarations import enclosing_method, outermost_class, parameters
from ..syntax.node import Node
from ..syntax.parser import ParserMissing, parse


@dataclass(frozen=True)
class Shape:
    """owner: the class body's offset, None when unread; parameters: per line, the method's (name, type) there."""
    owner: int | None = None
    returns: str | None = None
    parameters: dict[int, tuple[tuple[str, str | None], ...]] = field(default_factory=dict)


def _type_of(declaration: Node) -> str | None:
    named = next((c.text for c in declaration.children if c.type in g.TYPES), None)
    return named.rstrip("?") if named else None


def _shape(root: Node, s: Scope) -> Shape:
    call = find_call(root, s.line, s.call, frozenset((read_engines().factory,)), s.engineType)
    if call is None:
        return Shape()
    method, owner = enclosing_method(call), outermost_class(call)
    on_line: dict[int, list[tuple[str, str | None]]] = {}
    for name, p in parameters(method):
        on_line.setdefault(p.line, []).append((name, _type_of(p)))
    return Shape(owner.start if owner is not None else None, _type_of(method) if method is not None else None,
                 {line: tuple(found) for line, found in on_line.items()})


class Files:
    """One file's text and tree, read when first asked; links need them only in files with several scopes."""

    def __init__(self, root: Path):
        self.root, self.lines_of, self.trees, self.shapes = Path(root), {}, {}, {}

    def _source(self, file: str) -> str:
        return (self.root / file).read_text(errors="replace")

    def text(self, file: str, line: int) -> str:
        if file not in self.lines_of:
            self.lines_of[file] = self._source(file).splitlines()
        lines = self.lines_of[file]
        return lines[line - 1] if 1 <= line <= len(lines) else ""

    def _tree(self, file: str) -> Node | None:
        if file not in self.trees:
            try:
                self.trees[file] = parse(self._source(file), of_file(file))
            except ParserMissing:
                self.trees[file] = None
        return self.trees[file]

    def parameters_taken(self, s: Scope, r: Requirement) -> tuple[tuple[str, str | None], ...]:
        """The parameters on the requirement's line its step names; all of them when it names none (a local between)."""
        on_line = self.shape(s).parameters.get(r.line, ())
        step = self.text(s.file, r.at)
        return tuple(p for p in on_line if re.search(rf"\b{re.escape(p[0])}\b", step)) or on_line

    def shape(self, s: Scope) -> Shape:
        if s.id not in self.shapes:
            tree = self._tree(s.file)
            self.shapes[s.id] = _shape(tree, s) if tree is not None else Shape()
        return self.shapes[s.id]
