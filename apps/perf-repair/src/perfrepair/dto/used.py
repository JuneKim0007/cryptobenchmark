"""used.json (schema 1): the device items the target apps need, each with the apps that need it and how."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from cryptobench.document import DocumentKind

SCHEMA_VERSION = 1
USED_DOC = DocumentKind("used.json", SCHEMA_VERSION)
# in order of strength: a site resolves to it, it shares a group with one, it may join a pending one's group, or a
# broken one may upgrade to it
SITE, GROUP, CANDIDATE, UPGRADE = "site", "group", "candidate", "upgrade"
VIA = (SITE, GROUP, CANDIDATE, UPGRADE)


@dataclass(frozen=True)
class AppUse:
    sites: int
    matched: int


@dataclass(frozen=True)
class UsedItem:
    item: str
    via: str
    apps: tuple[str, ...]


@dataclass(frozen=True)
class UsedSet:
    deviceItems: int
    apps: dict[str, AppUse]
    items: tuple[UsedItem, ...] = field(default_factory=tuple)

    @property
    def names(self) -> frozenset[str]:
        return frozenset(u.item for u in self.items)

    def count(self, via: str) -> int:
        return sum(u.via == via for u in self.items)

    def to_json(self) -> dict:
        return {"schemaVersion": SCHEMA_VERSION, "deviceItems": self.deviceItems,
                "apps": {a: {"sites": u.sites, "matched": u.matched} for a, u in sorted(self.apps.items())},
                "items": [{"item": u.item, "via": u.via, "apps": list(u.apps)} for u in self.items]}

    @classmethod
    def from_json(cls, doc: dict) -> "UsedSet":
        USED_DOC.check(doc)
        return cls(int(doc["deviceItems"]), {a: AppUse(int(u["sites"]), int(u["matched"])) for a, u in doc["apps"].items()},
                   tuple(UsedItem(u["item"], u["via"], tuple(u["apps"])) for u in doc["items"]))


def names_digest(names) -> str:
    return hashlib.sha256("\n".join(sorted(names)).encode()).hexdigest()
