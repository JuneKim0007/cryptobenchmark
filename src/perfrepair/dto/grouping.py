"""Grouping: the item an agent sees, the static profile it never sees, and the families that frame both.

An item's `group` is null until an agent assigns it; everything else is fixed by static code.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Family:
    id: str
    type: str
    keyKind: str
    description: str


@dataclass(frozen=True)
class Item:
    id: int
    type: str
    name: str
    provider: str
    family: str
    resolved: str | None = None
    group: str | None = None

    @property
    def qualified(self) -> str:
        return f"{self.type}|{self.name}|{self.provider}"

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, d: dict) -> "Item":
        return cls(int(d["id"]), d["type"], d["name"], d["provider"], d["family"], d.get("resolved"), d.get("group"))


@dataclass(frozen=True)
class Profile:
    keyKind: str
    keyKindFrom: str
    instantiates: bool
    runs: bool
    reason: str | None = None
    defaultKeySize: int | None = None
    keyAlgorithm: str | None = None
    keyProvider: str | None = None
    bareName: bool = False
    measured: bool = False
    preparedKeySizes: tuple[int, ...] = field(default_factory=tuple)

    def to_json(self) -> dict:
        d = asdict(self)
        d["preparedKeySizes"] = list(self.preparedKeySizes)
        return d

    @classmethod
    def from_json(cls, d: dict) -> "Profile":
        return cls(**{**d, "preparedKeySizes": tuple(d.get("preparedKeySizes") or ())})


def items_document(items: list[Item]) -> dict:
    return {"schemaVersion": SCHEMA_VERSION, "items": [i.to_json() for i in items]}


def profiles_document(profiles: dict[int, Profile]) -> dict:
    return {"schemaVersion": SCHEMA_VERSION, "profiles": {str(k): p.to_json() for k, p in sorted(profiles.items())}}


def read_items(doc: dict) -> list[Item]:
    if doc.get("schemaVersion") != SCHEMA_VERSION:
        raise ValueError(f"items schemaVersion {doc.get('schemaVersion')} is not {SCHEMA_VERSION}")
    return [Item.from_json(d) for d in doc["items"]]


def read_profiles(doc: dict) -> dict[int, Profile]:
    if doc.get("schemaVersion") != SCHEMA_VERSION:
        raise ValueError(f"profiles schemaVersion {doc.get('schemaVersion')} is not {SCHEMA_VERSION}")
    return {int(k): Profile.from_json(v) for k, v in doc["profiles"].items()}
