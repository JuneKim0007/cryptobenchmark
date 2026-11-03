"""gaps.json: for one scope, what code could not close and the lines it can offer for each; the model chooses among them."""
from __future__ import annotations

from dataclasses import asdict, dataclass

GAPS_SCHEMA_VERSION = 1
GAP_PREFIX, CANDIDATE_PREFIX, UNKNOWN_CHOICE, UNKNOWN_ORIGIN = "G", "C", "unknown", "unknown"
USE_GAP = "use"
FIELD_WRITE, CALLER_ARGUMENT, RETURNED, PART, OBJECT_REFERENCE, HELPER_CALLER = (
    "field_write", "caller_argument", "returned", "part", "object_reference", "helper_caller")
HOWS = (FIELD_WRITE, CALLER_ARGUMENT, RETURNED, PART, OBJECT_REFERENCE, HELPER_CALLER)
# a use gap's origin says how the object reaches the chosen line
USE_ORIGINS = ("parameter", "field", "same_class_call", "other_call", UNKNOWN_ORIGIN)


@dataclass(frozen=True)
class Answer:
    """One gap's answer: the candidate chosen, or UNKNOWN_CHOICE, and its origin."""
    gap: str
    choice: str
    origin: str


@dataclass(frozen=True)
class Candidate:
    """One line code reached: how it got there, the text, and what code itself reads the value there as."""
    id: str
    how: str
    file: str
    line: int
    text: str
    reads: str


@dataclass(frozen=True)
class Gap:
    """name: a requirement's, or USE_GAP; origin, line, at: the requirement it completes; a use gap's are the anchor's."""
    id: str
    name: str
    origin: str
    line: int
    at: int
    candidates: tuple[Candidate, ...] = ()
    over_budget: bool = False

    @property
    def requirement(self) -> tuple[str, str, int, int]:
        return self.name, self.origin, self.line, self.at

    @classmethod
    def from_json(cls, d: dict) -> "Gap":
        return cls(d["id"], d["name"], d["origin"], d["line"], d["at"], tuple(Candidate(**c) for c in d["candidates"]),
                   d["over_budget"])


@dataclass(frozen=True)
class Statement:
    line: int
    text: str


@dataclass(frozen=True)
class Body:
    """At most one other method or class body per scope, code-selected and capped; start is its first line's number."""
    file: str
    start: int
    lines: tuple[str, ...]

    @classmethod
    def from_json(cls, d: dict | None) -> "Body | None":
        return None if d is None else cls(d["file"], d["start"], tuple(d["lines"]))


@dataclass(frozen=True)
class ScopeGaps:
    scope: str
    file: str
    function: str
    anchor: Statement
    included: tuple[Statement, ...]
    gaps: tuple[Gap, ...]
    body: Body | None = None

    @property
    def key(self) -> str:
        return self.scope

    @property
    def offered(self) -> tuple[Gap, ...]:
        return tuple(g for g in self.gaps if g.candidates)

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, d: dict) -> "ScopeGaps":
        return cls(d["scope"], d["file"], d["function"], Statement(**d["anchor"]),
                   tuple(Statement(**s) for s in d["included"]), tuple(Gap.from_json(g) for g in d["gaps"]),
                   Body.from_json(d.get("body")))


def read_gaps(doc: dict) -> list[ScopeGaps]:
    if doc.get("schemaVersion") != GAPS_SCHEMA_VERSION:
        raise ValueError(f"gaps schemaVersion {doc.get('schemaVersion')} is not {GAPS_SCHEMA_VERSION}")
    return [ScopeGaps.from_json(s) for s in doc["scopes"]]
