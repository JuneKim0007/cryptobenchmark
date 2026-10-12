from __future__ import annotations

from dataclasses import asdict, dataclass, field

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Amendment:
    group: str
    description: str


@dataclass(frozen=True)
class Answer:
    group: str = ""
    newGroupId: str = ""
    newGroupDescription: str = ""
    amend: tuple[Amendment, ...] = ()
    reason: str = ""

    @property
    def joins(self) -> bool:
        return bool(self.group)

    @property
    def target(self) -> str:
        return self.group or self.newGroupId

    def to_json(self) -> dict:
        return {"group": self.group, "newGroup": {"id": self.newGroupId, "description": self.newGroupDescription},
                "amend": [asdict(a) for a in self.amend], "reason": self.reason}

    @classmethod
    def from_json(cls, d: dict) -> "Answer":
        new = d.get("newGroup") or {}
        return cls(d.get("group") or "", new.get("id") or "", new.get("description") or "",
                   tuple(Amendment(a["group"], a["description"]) for a in d.get("amend") or ()), d.get("reason") or "")


@dataclass
class Group:
    family: str
    description: str
    members: list[int] = field(default_factory=list)


@dataclass
class Knowledge:
    version: int = 0
    groups: dict[str, Group] = field(default_factory=dict)
    dropped: list[int] = field(default_factory=list)

    def group_of(self, item: int) -> str | None:
        return next((gid for gid, g in self.groups.items() if item in g.members), None)

    def in_family(self, family: str) -> dict[str, Group]:
        return {gid: g for gid, g in self.groups.items() if g.family == family}

    def to_json(self) -> dict:
        return {"schemaVersion": SCHEMA_VERSION, "version": self.version,
                "groups": {gid: asdict(g) for gid, g in sorted(self.groups.items())}, "dropped": sorted(self.dropped)}

    @classmethod
    def from_json(cls, doc: dict) -> "Knowledge":
        if doc.get("schemaVersion") != SCHEMA_VERSION:
            raise ValueError(f"knowledge schemaVersion {doc.get('schemaVersion')} is not {SCHEMA_VERSION}")
        return cls(int(doc["version"]), {gid: Group(**g) for gid, g in doc["groups"].items()}, list(doc["dropped"]))
