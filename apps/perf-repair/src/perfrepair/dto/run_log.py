from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .document import DocumentKind

SCHEMA_VERSION = 1
RUN_LOG_DOC = DocumentKind("run log", SCHEMA_VERSION)
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
        RUN_LOG_DOC.check(doc)
        return cls([LogEntry.from_json(e) for e in doc.get("entries") or []])
