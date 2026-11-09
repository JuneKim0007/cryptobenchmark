from __future__ import annotations

from dataclasses import dataclass, field

from cryptobench.catalogue.document import DocumentKind

# 3: the tier asked and the model that answered replace gateway, model, effort
SCHEMA_VERSION = 3
OUTBOX_RECORD_DOC = DocumentKind("outbox record", SCHEMA_VERSION, "{name} schemaVersion {found} is not {version}")
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
    # the tier that gave the committed answer (gateway, model, effort, webSearch), and the model the provider named
    tier: dict = field(default_factory=dict)
    answered: str | None = None
    # the digest of the evidence the item was decided on, for a kind that declares one
    evidence: str | None = None

    @property
    def model(self) -> str:
        return self.answered or self.tier.get("model") or ""

    def to_json(self) -> dict:
        return {"schemaVersion": SCHEMA_VERSION, "seq": self.seq, "item": self.item, "outcome": self.outcome,
                "session": self.session, "turn": self.turn, "decision": self.decision, "problems": list(self.problems),
                "tier": dict(self.tier), "answered": self.answered,
                **({"evidence": self.evidence} if self.evidence is not None else {})}

    @classmethod
    def from_json(cls, d: dict) -> "OutboxRecord":
        OUTBOX_RECORD_DOC.check(d)
        if d.get("outcome") not in OUTCOMES:
            raise ValueError(f"outbox record {d.get('seq')}: outcome {d.get('outcome')!r} is not one of {OUTCOMES}")
        if (d["outcome"] == "decided") != (d.get("decision") is not None):
            raise ValueError(f"outbox record {d.get('seq')}: a decided record carries a decision, a dropped one none")
        return cls(int(d["seq"]), str(d["item"]), d["outcome"], int(d["session"]), int(d["turn"]),
                   d.get("decision"), tuple(d.get("problems") or ()), dict(d.get("tier") or {}), d.get("answered"),
                   d.get("evidence"))
