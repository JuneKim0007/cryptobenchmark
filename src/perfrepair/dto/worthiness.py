"""Test-worthiness: the measured evidence for one primitive group, and the verdict on it.

Evidence is computed by code (result/evidence.py) and handed to the model as is; the model only
decides. A pair reads "replace `from` with `to`"; its ratios are `to` ÷ `from`, so < 1 is better.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .measurement import Summary

SCHEMA_VERSION = 1
DECISIONS = ("test", "skip")
VERDICTS = ("test", "skip", "not_comparable", "no_improvement")
SOURCES = ("llm", "static", "fallback")


@dataclass(frozen=True)
class MemberStats:
    rowId: str
    itemId: str
    provider: str
    algorithm: str
    timeNs: Summary | None
    allocations: float | None


@dataclass(frozen=True)
class PairMetrics:
    fromItem: str
    toItem: str
    timeRatio: float
    iqrOverlap: bool
    allocationRatio: float | None


@dataclass(frozen=True)
class Configuration:
    operation: str
    keySize: int | None
    inputSize: int | None
    phase: str | None
    members: tuple[MemberStats, ...]
    pairs: tuple[PairMetrics, ...]


@dataclass(frozen=True)
class GroupEvidence:
    groupId: str
    label: str
    type: str
    family: str
    configurations: tuple[Configuration, ...]

    @property
    def key(self) -> str:
        return self.groupId

    @property
    def members(self) -> tuple[str, ...]:
        return tuple(sorted({m.itemId for c in self.configurations for m in c.members}))


@dataclass(frozen=True)
class Pair:
    fromItem: str
    toItem: str
    reason: str


@dataclass(frozen=True)
class Verdict:
    groupId: str
    mode: str
    decision: str
    reason: str
    source: str
    proxy: bool
    pairs: tuple[Pair, ...] = ()

    def to_json(self) -> dict:
        return {"groupId": self.groupId, "mode": self.mode, "decision": self.decision, "reason": self.reason,
                "source": self.source, "proxy": self.proxy,
                "pairs": [{"from": p.fromItem, "to": p.toItem, "reason": p.reason} for p in self.pairs]}

    @classmethod
    def from_json(cls, d: dict) -> "Verdict":
        if d["decision"] not in VERDICTS or d["source"] not in SOURCES:
            raise ValueError(f"verdict {d['groupId']}: decision {d['decision']!r} or source {d['source']!r} unknown")
        return cls(d["groupId"], d["mode"], d["decision"], d["reason"], d["source"], bool(d["proxy"]),
                   tuple(Pair(p["from"], p["to"], p["reason"]) for p in d.get("pairs") or ()))


@dataclass
class Verdicts:
    mode: str
    version: int = 0
    verdicts: dict[str, Verdict] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {"schemaVersion": SCHEMA_VERSION, "mode": self.mode, "version": self.version,
                "verdicts": [v.to_json() for v in self.verdicts.values()]}

    @classmethod
    def from_json(cls, doc: dict) -> "Verdicts":
        if doc.get("schemaVersion") != SCHEMA_VERSION:
            raise ValueError(f"verdicts schemaVersion {doc.get('schemaVersion')} is not {SCHEMA_VERSION}")
        vs = [Verdict.from_json(v) for v in doc.get("verdicts") or []]
        return cls(doc["mode"], int(doc.get("version", 0)), {v.groupId: v for v in vs})
