"""Event: one line of log/events.jsonl; the views and the summary are computed from these only."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

SCHEMA_VERSION = 1
KINDS = ("static", "model")
# a step's start and end; a model turn and the item's decision; a command's run, its coded error or bug; a log record
START, END, TURN, DECISION = "start", "end", "turn", "decision"
RUN_START, RUN_END, ERROR, BUG, LOG = "run_start", "run_end", "error", "bug", "log"
OPTIONAL = (str, type(None))
# field → the types its value may take; every field is present on every line
FIELDS: dict[str, tuple[type, ...]] = {
    "schemaVersion": (int,), "ts": (str,), "run": (str,), "stage": (str,), "step": (str,), "event": (str,),
    "kind": (str,), "item": OPTIONAL, "app": OPTIONAL, "outcome": OPTIONAL, "durationMs": (int, type(None)),
    "tokens": (dict, type(None)), "costUsd": (int, float, type(None)), "ref": OPTIONAL, "detail": (str,),
    "data": (dict,),
}


@dataclass(frozen=True)
class Event:
    ts: str
    run: str
    stage: str
    step: str
    event: str
    kind: str = "static"
    item: str | None = None
    app: str | None = None
    outcome: str | None = None
    durationMs: int | None = None
    tokens: dict | None = None
    costUsd: float | None = None
    ref: str | None = None
    detail: str = ""
    data: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        return {"schemaVersion": SCHEMA_VERSION, **asdict(self)}

    @classmethod
    def from_json(cls, d: dict) -> "Event":
        if d.get("schemaVersion") != SCHEMA_VERSION:
            raise ValueError(f"event schemaVersion {d.get('schemaVersion')} is not {SCHEMA_VERSION}")
        return cls(**{k: v for k, v in d.items() if k != "schemaVersion"})
