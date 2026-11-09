from __future__ import annotations

from .paths import DATA
from pathlib import Path

from ..document import AT_PATH, DocumentKind
from .grouping import Family

CATALOG = DATA / "families.yaml"
SCHEMA_VERSION = 1
FAMILIES_DOC = DocumentKind("families", SCHEMA_VERSION, AT_PATH)
UNIDENTIFIED, ANY_TYPE = "unidentified", "any"


class Families:
    """all: the families; by_id also holds unidentified, the place of an item no family fits."""

    def __init__(self, families: list[Family], unidentified: Family):
        self.all, self.unidentified = families, unidentified
        self.by_id = {f.id: f for f in (*families, unidentified)}
        self._by_key = {(f.type, f.keyKind): f for f in families}
        if len(self.by_id) != len(families) + 1 or len(self._by_key) != len(families):
            raise ValueError("families: duplicate id or (type, keyKind)")

    @classmethod
    def load(cls, path: Path = CATALOG) -> "Families":
        doc = FAMILIES_DOC.read(path)
        return cls([Family(**f) for f in doc["families"]], Family(**doc["unidentified"]))

    @property
    def types(self) -> set[str]:
        return {f.type for f in self.all}

    def key_kinds(self, engine_type: str) -> list[str]:
        return [f.keyKind for f in self.all if f.type == engine_type]

    def of(self, engine_type: str, key_kind: str) -> Family | None:
        return self._by_key.get((engine_type, key_kind))
