from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .document import DocumentKind
from .metrics import ESTIMATED, MEASURED

__all__ = ["ESTIMATED", "MEASURED", "Measurements", "SCHEMA_VERSION", "Summary"]
# 4: every metric under its benchmark.json name (allocations became allocationCount); one without runs is absent
SCHEMA_VERSION = 4
MEASUREMENTS_DOC = DocumentKind("measurements", SCHEMA_VERSION)


@dataclass(frozen=True)
class Summary:
    median: float
    p25: float
    p75: float
    cv: float | None
    n: int
    low: float | None
    high: float | None
    processes: tuple[tuple[float, ...], ...] = ()
    kind: str | None = None

    def to_json(self) -> dict:
        kept = {k: v for k, v in asdict(self).items() if k != "kind" or v is not None}
        return kept | {"processes": [list(p) for p in self.processes]}

    @classmethod
    def from_json(cls, d: dict) -> "Summary":
        return cls(d["median"], d["p25"], d["p75"], d.get("cv"), d["n"], d.get("low"), d.get("high"),
                   tuple(tuple(p) for p in d.get("processes") or ()), d.get("kind"))


@dataclass
class Measurements:
    runtime: dict
    comparability: list[str]
    byRow: dict[str, dict[str, Summary]] = field(default_factory=dict)
    # per row its benchmark.json `thermal` and thermalThrottleSleepSeconds; a host run has none; not decision evidence
    thermal: dict[str, dict] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {"schemaVersion": SCHEMA_VERSION, "runtime": self.runtime, "comparability": self.comparability,
                "measurements": {rid: {k: s.to_json() for k, s in m.items()}
                                 for rid, m in self.byRow.items()}} | ({"thermal": self.thermal} if self.thermal else {})

    @classmethod
    def from_json(cls, doc: dict) -> "Measurements":
        MEASUREMENTS_DOC.check(doc)
        return cls(doc.get("runtime") or {}, list(doc.get("comparability") or []),
                   {rid: {k: Summary.from_json(s) for k, s in m.items()}
                    for rid, m in (doc.get("measurements") or {}).items()}, doc.get("thermal") or {})
