"""The app source a scoping invariant reads: a file as Code, the function around a line, the calls a line holds."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ...scope.extract import Function, enclosing, functions
from ...source.code import Code
from ...source.language import of_file


@dataclass(frozen=True)
class Call:
    receiver: str | None
    open_paren: int


class Sources:
    """One project root's files, each read once; a file it cannot read is None, and the rule says so."""

    def __init__(self, root: Path | None):
        self.root, self._files = root, {}

    def code(self, file: str) -> Code | None:
        if file not in self._files:
            path = self.root / file if self.root is not None else None
            language = of_file(file)
            ok = path is not None and language is not None and path.is_file()
            self._files[file] = Code.of(path.read_text(encoding="utf-8", errors="replace"), language) if ok else None
        return self._files[file]

    def why_not(self, file: str) -> str:
        return "no project root" if self.root is None else f"source not readable: {self.root / file}"


def line_start(code: Code, line: int) -> int:
    return code.starts[line - 1] if 1 <= line <= len(code.starts) else len(code.text)


def line_end(code: Code, line: int) -> int:
    return code.starts[line] - 1 if line < len(code.starts) else len(code.text)


def function_at(code: Code, line: int) -> Function | None:
    a, text = line_start(code, line), code.line_text(line)
    return enclosing(functions(code), a + len(text) - len(text.lstrip()))


def calls_on(code: Code, line: int, name: str) -> list[Call]:
    """Every `name(` the line's code holds, with the simple name it is called on, if any."""
    a, b = line_start(code, line), line_end(code, line)
    rx = re.compile(r"(?:(\w+)\s*\??\.\s*)?\b" + re.escape(name) + r"\s*\(")
    return [Call(m.group(1), m.end() - 1) for m in rx.finditer(code.masked, a, b)]


def body(code: Code, f: Function) -> str:
    return code.masked[f.start:f.end]


def squeezed(text: str) -> str:
    return re.sub(r"\s+", "", text)
