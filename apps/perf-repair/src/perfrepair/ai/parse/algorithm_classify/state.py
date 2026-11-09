from __future__ import annotations

from dataclasses import dataclass, field

from ....dto.classify import ACCEPTED, SCHEMA_VERSION, UNSURE, Answer, Batch
from ....dto.decision import OutboxRecord
from cryptobench.document import DocumentKind
from ....dto.screen import Verdict, with_answer

CLASSIFIED_DOC = DocumentKind("classified", SCHEMA_VERSION)


@dataclass
class Classified:
    answers: dict[int, Answer] = field(default_factory=dict)
    version: int = 0

    def to_json(self) -> dict:
        return {"schemaVersion": SCHEMA_VERSION, "version": self.version,
                "answers": {str(k): a.to_json() for k, a in sorted(self.answers.items())}}

    @classmethod
    def from_json(cls, d: dict) -> "Classified":
        CLASSIFIED_DOC.check(d)
        return cls({int(k): Answer.from_json(a) for k, a in d["answers"].items()}, d["version"])


def apply(state: Classified, batch: Batch, record: OutboxRecord) -> None:
    if record.outcome == "decided":
        for a in record.decision["answers"]:
            state.answers[a["id"]] = Answer.from_json(a)
    else:
        for i in batch.ids:
            state.answers[i] = Answer(i, UNSURE, "dropped: " + "; ".join(record.problems))
    state.version += 1


def reviewed(verdicts: dict[int, Verdict], state: Classified, fingerprint: str) -> dict[int, Verdict]:
    return {k: with_answer(v, state.answers[k].answer, state.answers[k].reason, fingerprint)
            if k in state.answers else v for k, v in verdicts.items()}


def candidates(state: Classified, batches: list[Batch], fingerprint: str) -> dict:
    """registry-candidates.yaml: each accepted answer, for a person to confirm as a sourced catalog row."""
    evidence = {e.id: e for b in batches for e in b.members}
    rows = [{"id": a.id, "type": evidence[a.id].type, "name": evidence[a.id].name,
             "canonical": evidence[a.id].canonical, "provider": evidence[a.id].provider, "reason": a.reason,
             "fingerprint": fingerprint}
            for a in sorted(state.answers.values(), key=lambda a: a.id) if a.answer == ACCEPTED]
    return {"schemaVersion": SCHEMA_VERSION, "candidates": rows}
