"""Link and Unit: primitive objects decided, swapped and measured together; the links that say why, with lines on both sides."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .site import Dossier

UNITS_SCHEMA_VERSION = 1
SHARED_KEY, INVERSE, PRODUCER_CONSUMER = "shared_key", "inverse", "producer_consumer"
LINK_KINDS = (SHARED_KEY, INVERSE, PRODUCER_CONSUMER)
# what the two sides have in common: per kind, the evidence that may back it
LINK_VIA = {SHARED_KEY: ("field", "parameter", "same_class_call", "other_call", "generated", "derived", "keystore", "decoded",
                         "storage"),
            INVERSE: ("key", "input", "producer", "parameter"),
            PRODUCER_CONSUMER: ("line", "call", "field", "parameter")}
MEMBER_PREFIX = "S"


def unit_id(app: str, members: list[str]) -> str:
    return hashlib.sha256("\0".join([app, *sorted(members)]).encode()).hexdigest()[:12]


@dataclass(frozen=True)
class Link:
    """a, b: scope ids, the producing side first when the kind has a direction; aLines, bLines: the evidence on each."""
    kind: str
    a: str
    b: str
    aLines: tuple[int, ...]
    bLines: tuple[int, ...]
    via: str

    def to_json(self) -> dict:
        return {"kind": self.kind, "a": self.a, "b": self.b, "aLines": list(self.aLines), "bLines": list(self.bLines),
                "via": self.via}

    @classmethod
    def from_json(cls, d: dict) -> "Link":
        return cls(d["kind"], d["a"], d["b"], tuple(d["aLines"]), tuple(d["bLines"]), d["via"])


@dataclass(frozen=True)
class Unit:
    """members in file and line order; a scope with no link is a unit of one. sharedFunction: the other units with a
    member in one of this unit's functions."""
    id: str
    members: tuple[str, ...]
    links: tuple[Link, ...] = ()
    sharedFunction: tuple[str, ...] = ()

    def to_json(self) -> dict:
        return {"id": self.id, "members": list(self.members), "links": [k.to_json() for k in self.links],
                "sharedFunction": list(self.sharedFunction)}

    @classmethod
    def from_json(cls, d: dict) -> "Unit":
        return cls(d["id"], tuple(d["members"]), tuple(Link.from_json(k) for k in d["links"]), tuple(d["sharedFunction"]))


def read_units(doc: dict) -> list[Unit]:
    if doc.get("schemaVersion") != UNITS_SCHEMA_VERSION:
        raise ValueError(f"units schemaVersion {doc.get('schemaVersion')} is not {UNITS_SCHEMA_VERSION}")
    return [Unit.from_json(u) for u in doc["units"]]


def units_by_scope(units: list[Unit]) -> dict[str, Unit]:
    return {member: u for u in units for member in u.members}


@dataclass(frozen=True)
class UnitDossiers:
    """One decision: a unit and the dossier of each member, in the unit's member order."""
    unit: Unit
    dossiers: tuple[Dossier, ...]

    @property
    def key(self) -> str:
        return self.unit.id

    def aliased(self) -> dict[str, Dossier]:
        return {f"{MEMBER_PREFIX}{n}": d for n, d in enumerate(self.dossiers, 1)}
