"""One committed decision of any kind: the outbox record. The outbox is the only commit; a kind's state
is the projection of its records."""
from __future__ import annotations

from dataclasses import dataclass

SCHEMA_VERSION = 1
OUTCOMES = ("decided", "dropped")


@dataclass(frozen=True)
class OutboxRecord:
    seq: int
    item: str
    outcome: str
    session: int
    turn: int
    decision: dict | None = None
    problems: tuple[str, ...] = ()

    def to_json(self) -> dict:
        return {"schemaVersion": SCHEMA_VERSION, "seq": self.seq, "item": self.item, "outcome": self.outcome,
                "session": self.session, "turn": self.turn, "decision": self.decision, "problems": list(self.problems)}

    @classmethod
    def from_json(cls, d: dict) -> "OutboxRecord":
        if d.get("schemaVersion") != SCHEMA_VERSION:
            raise ValueError(f"outbox record schemaVersion {d.get('schemaVersion')} is not {SCHEMA_VERSION}")
        if d.get("outcome") not in OUTCOMES:
            raise ValueError(f"outbox record {d.get('seq')}: outcome {d.get('outcome')!r} is not one of {OUTCOMES}")
        if (d["outcome"] == "decided") != (d.get("decision") is not None):
            raise ValueError(f"outbox record {d.get('seq')}: a decided record carries a decision, a dropped one none")
        return cls(int(d["seq"]), str(d["item"]), d["outcome"], int(d["session"]), int(d["turn"]),
                   d.get("decision"), tuple(d.get("problems") or ()))
