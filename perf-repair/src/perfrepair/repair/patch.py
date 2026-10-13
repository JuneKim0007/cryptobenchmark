"""One call site rewritten to its replacement: only the string literals of the getInstance call change."""
from __future__ import annotations

import difflib
from dataclasses import asdict, dataclass
from pathlib import Path

from .candidates import Candidate


@dataclass(frozen=True)
class Patch:
    file: str
    line: int
    before: str
    after: str

    def to_json(self) -> dict:
        return asdict(self)

    def diff(self, root: Path) -> str:
        lines = (root / self.file).read_text().splitlines(keepends=True)
        edited = lines[:self.line - 1] + [lines[self.line - 1].replace(self.before, self.after, 1)] + lines[self.line:]
        return "".join(difflib.unified_diff(lines, edited, f"a/{self.file}", f"b/{self.file}"))


def rewrite(site: Candidate, resolved_provider: str, name: str, provider: str, root: Path) -> Patch:
    """TEMP: literal arguments on one line only; a non-literal call is not rewritten."""
    if site.algorithm is None:
        raise ValueError(f"{site.file}:{site.line}: algorithm is not a literal")
    text = (root / site.file).read_text().splitlines()[site.line - 1]
    call = text[text.index(f"{site.engineType}.getInstance("):]
    call = call[:call.index(")") + 1]
    if site.provider is None and "," in call:
        raise ValueError(f"{site.file}:{site.line}: provider is not a literal")
    new = call.replace(f'"{site.algorithm}"', f'"{name}"', 1)
    if site.provider is not None:
        new = new.replace(f'"{site.provider}"', f'"{provider}"', 1)
    elif provider != resolved_provider:
        new = new.replace(f'"{name}"', f'"{name}", "{provider}"', 1)
    return Patch(site.file, site.line, call, new)
