from __future__ import annotations

from dataclasses import asdict, dataclass

from .signature import Signature

SCHEMA_VERSION = 1
CURSOR_SCHEMA_VERSION = 1
# 4: signature
PROFILES_SCHEMA_VERSION = 4
SEPARATOR = "|"
KEY_APP_HELD, KEY_PROVIDER_HELD, KEY_UNKNOWN = "app_held", "provider_held", "unknown"
KEY_CONTRACTS = (KEY_APP_HELD, KEY_PROVIDER_HELD, KEY_UNKNOWN)
KEY_LABELS = {KEY_APP_HELD: "application-held", KEY_PROVIDER_HELD: "inside the provider"}


def qualified(engine_type: str, name: str, provider: str) -> str:
    return SEPARATOR.join((engine_type, name, provider))


def parse_qualified(text: str) -> tuple[str, str, str]:
    engine_type, name, provider = text.split(SEPARATOR)
    return engine_type, name, provider


def provider_of(item: str) -> str:
    return parse_qualified(item)[2]


def algorithm_of(item: str) -> str:
    return parse_qualified(item)[1]


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
        return qualified(self.type, self.name, self.provider)

    @property
    def key(self) -> str:
        """What a record names: ids are positional and move when items change; a new family makes it a new question."""
        return SEPARATOR.join((self.family, self.qualified))

    @classmethod
    def from_key(cls, key: str) -> "Item":
        """An item a record names that items.json no longer holds; id 0 is no item."""
        parts = key.split(SEPARATOR)
        if len(parts) != 4:
            raise ValueError(f"outbox_unkeyed: a record names item {key!r}; run grouping assign to rekey its outbox")
        family, engine_type, name, provider = parts
        return cls(0, engine_type, name, provider, family)

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
    measured: bool | None = None
    preparedKeySizes: tuple[int, ...] | None = None
    keyContract: str = KEY_UNKNOWN
    signature: Signature | None = None

    def to_json(self) -> dict:
        d = asdict(self)
        d["preparedKeySizes"] = None if self.preparedKeySizes is None else list(self.preparedKeySizes)
        d["signature"] = None if self.signature is None else self.signature.to_json()
        return d

    @classmethod
    def from_json(cls, d: dict) -> "Profile":
        sizes, signature = d.get("preparedKeySizes"), d.get("signature")
        return cls(**{**d, "preparedKeySizes": None if sizes is None else tuple(sizes),
                      "signature": None if signature is None else Signature.from_json(signature)})


def items_document(items: list[Item]) -> dict:
    return {"schemaVersion": SCHEMA_VERSION, "items": [i.to_json() for i in items]}


def profiles_document(profiles: dict[int, Profile]) -> dict:
    return {"schemaVersion": PROFILES_SCHEMA_VERSION, "profiles": {str(k): p.to_json() for k, p in sorted(profiles.items())}}


def read_items(doc: dict) -> list[Item]:
    if doc.get("schemaVersion") != SCHEMA_VERSION:
        raise ValueError(f"items schemaVersion {doc.get('schemaVersion')} is not {SCHEMA_VERSION}")
    return [Item.from_json(d) for d in doc["items"]]


def read_profiles(doc: dict) -> dict[int, Profile]:
    if doc.get("schemaVersion") != PROFILES_SCHEMA_VERSION:
        raise ValueError(f"profiles schemaVersion {doc.get('schemaVersion')} is not {PROFILES_SCHEMA_VERSION}; rerun grouping build")
    return {int(k): Profile.from_json(v) for k, v in doc["profiles"].items()}
