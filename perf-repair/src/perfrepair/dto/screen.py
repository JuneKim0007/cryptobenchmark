from __future__ import annotations

from dataclasses import asdict, dataclass

SCHEMA_VERSION = 1
BROKEN, PLATFORM_DEPRECATED, ACCEPTED, UNKNOWN = "broken", "platform_deprecated", "accepted", "unknown"
STATUSES = (BROKEN, PLATFORM_DEPRECATED, ACCEPTED, UNKNOWN)


@dataclass(frozen=True)
class Verdict:
    status: str
    reason: str
    source: str | None = None

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, d: dict) -> "Verdict":
        return cls(d["status"], d["reason"], d.get("source"))


def screen_document(verdicts: dict[int, Verdict]) -> dict:
    return {"schemaVersion": SCHEMA_VERSION, "verdicts": {str(k): v.to_json() for k, v in sorted(verdicts.items())}}


def read_screen(doc: dict) -> dict[int, Verdict]:
    if doc.get("schemaVersion") != SCHEMA_VERSION:
        raise ValueError(f"screen schemaVersion {doc.get('schemaVersion')} is not {SCHEMA_VERSION}")
    return {int(k): Verdict.from_json(v) for k, v in doc["verdicts"].items()}
