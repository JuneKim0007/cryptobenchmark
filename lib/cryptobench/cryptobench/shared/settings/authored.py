"""The authored global.yaml, read once: its document, providers.bundled checked, the test set beside it as Kotlin finds it, the known vectors against it."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cryptobench.shared import paths
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.settings import bundled


@dataclass(frozen=True)
class Authored:
    """Fields are properties, so a caller meets only the refusals of what it reads."""
    path: Path
    document: dict

    @property
    def bundled(self) -> list[dict]:
        return bundled.entries(self.document, self.path)

    @property
    def known_vectors(self) -> Path | None:
        value = self._selected("knownVectors")
        return paths.against(self.path, value) if value else None

    @property
    def test_set(self) -> Path | None:
        """Kotlin's AuthoredFiles reads the same file, so its rule, not paths.against."""
        value = self._selected("testSet")
        return paths.beside(self.path, value) if value else None

    def _selected(self, key: str):
        return (self.document.get("selection") or {}).get(key)


def read(global_file: Path | str) -> Authored:
    return Authored(Path(global_file), read_yaml(global_file))
