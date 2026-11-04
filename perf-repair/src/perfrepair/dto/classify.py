from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .document import DocumentKind

SCHEMA_VERSION = 1
BATCHES_DOC = DocumentKind("batches", SCHEMA_VERSION)
DEPRECATED, ACCEPTED, UNSURE = "deprecated", "accepted", "unsure"
ANSWERS = (DEPRECATED, ACCEPTED, UNSURE)
SEPARATOR = ","


@dataclass(frozen=True)
class Evidence:
    """What the classify model sees of one unknown item: identity and the recorded trial, nothing it must run."""
    id: int
    type: str
    name: str
    canonical: str
    provider: str
    family: str
    instantiates: bool
    error: str | None
    className: str | None
    attributes: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, d: dict) -> "Evidence":
        return cls(**d)


@dataclass(frozen=True)
class Batch:
    members: tuple[Evidence, ...]

    @property
    def key(self) -> str:
        return SEPARATOR.join(str(e.id) for e in self.members)

    @property
    def ids(self) -> tuple[int, ...]:
        return tuple(e.id for e in self.members)


@dataclass(frozen=True)
class Answer:
    id: int
    answer: str
    reason: str

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, d: dict) -> "Answer":
        return cls(int(d["id"]), d["answer"], d["reason"])


def batch_ids(key: str) -> list[int]:
    return [int(n) for n in key.split(SEPARATOR)]


def batches_document(batches: list[Batch]) -> dict:
    return {"schemaVersion": SCHEMA_VERSION, "batches": [[e.to_json() for e in b.members] for b in batches]}


def read_batches(doc: dict) -> list[Batch]:
    BATCHES_DOC.check(doc)
    return [Batch(tuple(Evidence.from_json(e) for e in b)) for b in doc["batches"]]
