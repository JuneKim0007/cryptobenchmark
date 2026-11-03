from __future__ import annotations

from dataclasses import asdict, dataclass, field

from ....dto.decision import OutboxRecord
from ....dto.gaps import UNKNOWN_CHOICE, UNKNOWN_ORIGIN, Answer, ScopeGaps

COMPLETED_SCHEMA_VERSION = 1


@dataclass
class Completed:
    """Per scope asked, one Answer per offered gap; dropped: the scopes whose every attempt failed, all unknown."""
    app: str
    answers: dict[str, tuple[Answer, ...]] = field(default_factory=dict)
    dropped: set[str] = field(default_factory=set)
    version: int = 0

    def to_json(self) -> dict:
        return {"schemaVersion": COMPLETED_SCHEMA_VERSION, "app": self.app, "version": self.version,
                "dropped": sorted(self.dropped),
                "answers": {k: [asdict(a) for a in v] for k, v in sorted(self.answers.items())}}

    @classmethod
    def from_json(cls, d: dict) -> "Completed":
        if d.get("schemaVersion") != COMPLETED_SCHEMA_VERSION:
            raise ValueError(f"completed schemaVersion {d.get('schemaVersion')} is not {COMPLETED_SCHEMA_VERSION}")
        return cls(d["app"], {k: tuple(Answer(**a) for a in v) for k, v in d["answers"].items()}, set(d["dropped"]),
                   d["version"])


def apply(state: Completed, entry: ScopeGaps, record: OutboxRecord) -> None:
    if record.outcome == "decided":
        state.answers[entry.key] = tuple(Answer(**a) for a in record.decision["answers"])
        state.dropped.discard(entry.key)
    else:
        state.answers[entry.key] = tuple(Answer(g.id, UNKNOWN_CHOICE, UNKNOWN_ORIGIN) for g in entry.offered)
        state.dropped.add(entry.key)
    state.version += 1
