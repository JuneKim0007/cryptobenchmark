"""The predefined families (families.yaml) and the lookup from (engine type, key kind) to one of them."""
from __future__ import annotations

from pathlib import Path

import yaml

from ...dto.grouping import Family

CATALOG = Path(__file__).with_name("families.yaml")


class Families:

    def __init__(self, families: list[Family]):
        self.all = families
        self.by_id = {f.id: f for f in families}
        self._by_key = {(f.type, f.keyKind): f for f in families}
        if len(self.by_id) != len(families) or len(self._by_key) != len(families):
            raise ValueError("families: duplicate id or (type, keyKind)")

    @classmethod
    def load(cls, path: Path = CATALOG) -> "Families":
        doc = yaml.safe_load(Path(path).read_text())
        if doc.get("schemaVersion") != 1:
            raise ValueError(f"{path}: schemaVersion {doc.get('schemaVersion')} is not 1")
        return cls([Family(**f) for f in doc["families"]])

    @property
    def types(self) -> set[str]:
        return {f.type for f in self.all}

    def key_kinds(self, engine_type: str) -> list[str]:
        return [f.keyKind for f in self.all if f.type == engine_type]

    def of(self, engine_type: str, key_kind: str) -> Family | None:
        return self._by_key.get((engine_type, key_kind))
