from __future__ import annotations

from dataclasses import asdict, dataclass, field

SCHEMA_VERSION = 2


@dataclass(frozen=True)
class Summary:
    median: float
    p25: float
    p75: float
    cv: float | None
    n: int
    low: float
    high: float

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, d: dict) -> "Summary":
        return cls(d["median"], d["p25"], d["p75"], d.get("cv"), d["n"], d["low"], d["high"])


@dataclass
class Measurements:
    runtime: dict
    comparability: list[str]
    byRow: dict[str, dict[str, Summary | None]] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {"schemaVersion": SCHEMA_VERSION, "runtime": self.runtime, "comparability": self.comparability,
                "measurements": {rid: {k: (s.to_json() if s else None) for k, s in m.items()}
                                 for rid, m in self.byRow.items()}}

    @classmethod
    def from_json(cls, doc: dict) -> "Measurements":
        if doc.get("schemaVersion") != SCHEMA_VERSION:
            raise ValueError(f"measurements schemaVersion {doc.get('schemaVersion')} is not {SCHEMA_VERSION}")
        return cls(doc.get("runtime") or {}, list(doc.get("comparability") or []),
                   {rid: {k: (Summary.from_json(s) if s else None) for k, s in m.items()}
                    for rid, m in (doc.get("measurements") or {}).items()})
