"""DocumentKind: a versioned document's accepted schemaVersion and the refusal its reader raises for another."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .coded import InputError

NAMED = "{name} schemaVersion {found} is not {version}"
AT_PATH = "{path}: schemaVersion {found} is not {version}"


@dataclass(frozen=True)
class DocumentKind:
    """message is each reader's own wording, kept until one shape is chosen (backlog R51); version may be a tuple."""
    name: str
    version: int | tuple[int, ...]
    message: str = NAMED
    error: type[InputError] = InputError

    def accepts(self, found: object) -> bool:
        return found in self.version if isinstance(self.version, tuple) else found == self.version

    def check(self, doc: dict, path: Path | str | None = None) -> dict:
        found = doc.get("schemaVersion")
        if not self.accepts(found):
            raise self.error(self.message.format(name=self.name, found=found, version=self.version, path=path), path,
                             f"schemaVersion {found!r} is not {self.version}")
        return doc
