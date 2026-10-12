"""What happened to each primitive in a run, deduplicated.

`status`:
  measured      a case produced samples
  skipped       preparation or config dropped it (skipped.yaml)
  refused       PlanCheck refused it before any timer (needs the refusals in a file the manifest lists)
  unmeasured    prepared, but no samples came back and no file says why
  not_runnable  the device registers the service but the trial could not run it
One entry per (status, stage, provider, type, algorithm, reason); `rowIds` lists the cases it covers,
`occurrences` how many raw records were folded into it.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

SCHEMA_VERSION = 1
STATUSES = ("measured", "skipped", "refused", "unmeasured", "not_runnable")


@dataclass(frozen=True)
class LogEntry:
    status: str
    stage: str | None
    provider: str | None
    type: str | None
    algorithm: str | None
    reason: str | None
    occurrences: int = 1
    rowIds: tuple[str, ...] = ()

    def to_json(self) -> dict:
        d = asdict(self)
        d["rowIds"] = list(self.rowIds)
        return d

    @classmethod
    def from_json(cls, d: dict) -> "LogEntry":
        if d["status"] not in STATUSES:
            raise ValueError(f"log status {d['status']!r} is not one of {STATUSES}")
        return cls(d["status"], d.get("stage"), d.get("provider"), d.get("type"), d.get("algorithm"),
                   d.get("reason"), int(d.get("occurrences", 1)), tuple(d.get("rowIds") or ()))


@dataclass
class RunLog:
    entries: list[LogEntry] = field(default_factory=list)

    def to_json(self) -> dict:
        return {"schemaVersion": SCHEMA_VERSION, "entries": [e.to_json() for e in self.entries]}

    @classmethod
    def from_json(cls, doc: dict) -> "RunLog":
        if doc.get("schemaVersion") != SCHEMA_VERSION:
            raise ValueError(f"run log schemaVersion {doc.get('schemaVersion')} is not {SCHEMA_VERSION}")
        return cls([LogEntry.from_json(e) for e in doc.get("entries") or []])
