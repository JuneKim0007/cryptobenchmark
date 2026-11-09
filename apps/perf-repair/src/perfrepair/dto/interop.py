"""interop_plan.yaml (perf-repair → cryptobenchmark) and interop.yaml (back); members are {type, algorithm, provider}."""
from __future__ import annotations

from dataclasses import dataclass

from cryptobench.catalogue.grouping import parse_qualified, qualified

SCHEMA_VERSION = 1
NOT_CHECKABLE = "not_checkable"
RESULTS = ("pass", "fail", NOT_CHECKABLE)
NOT_RUN = "not_run"
NOT_PLANNED = "not_planned"
STATUSES = ("checked", NOT_RUN)
PAIR_STATUSES = (*RESULTS, NOT_PLANNED, NOT_RUN)


def member(text: str) -> dict:
    engine_type, name, provider = parse_qualified(text)
    return {"type": engine_type, "algorithm": name, "provider": provider}


def member_name(d: dict) -> str:
    return qualified(d["type"], d["algorithm"], d["provider"])


@dataclass(frozen=True)
class PlannedPair:
    id: int
    group: str
    a: str
    b: str
    keySize: int | None = None

    def to_json(self) -> dict:
        d = {"id": self.id, "group": self.group, "a": member(self.a), "b": member(self.b)}
        return d if self.keySize is None else {**d, "keySize": self.keySize}

    @classmethod
    def from_json(cls, d: dict) -> "PlannedPair":
        return cls(int(d["id"]), d["group"], member_name(d["a"]), member_name(d["b"]), d.get("keySize"))


@dataclass(frozen=True)
class PairResult:
    id: int
    group: str
    a: str
    b: str
    result: str
    reason: str

    @property
    def members(self) -> frozenset[str]:
        return frozenset((self.a, self.b))

    def to_json(self) -> dict:
        return {"id": self.id, "group": self.group, "a": self.a, "b": self.b, "result": self.result, "reason": self.reason}

    @classmethod
    def from_json(cls, d: dict) -> "PairResult":
        return cls(int(d["id"]), d["group"], d["a"], d["b"], d["result"], d["reason"])

    @classmethod
    def from_interop(cls, d: dict) -> "PairResult":
        return cls(int(d["id"]), d["group"], member_name(d["a"]), member_name(d["b"]), d["result"], d.get("reason") or "")


def plan_document(pairs: list[PlannedPair], not_checkable: tuple[PairResult, ...] = ()) -> dict:
    document = {"schemaVersion": SCHEMA_VERSION, "pairs": [p.to_json() for p in pairs]}
    if not_checkable:
        document["notCheckable"] = [{"id": r.id, "group": r.group, "a": member(r.a), "b": member(r.b), "reason": r.reason}
                                    for r in not_checkable]
    return document


def not_checkable_results(plan: dict) -> list[PairResult]:
    """Pairs the plan holds back from the oracle; their result is known without running them."""
    return [PairResult.from_interop({**d, "result": NOT_CHECKABLE}) for d in plan.get("notCheckable") or []]


def interop_section(results: list[PairResult] | None) -> dict:
    if results is None:
        return {"status": NOT_RUN, "pairs": []}
    return {"status": "checked", "pairs": [r.to_json() for r in sorted(results, key=lambda r: r.id)]}


def section_results(groups: dict) -> tuple[str, list[PairResult]]:
    if "interop" not in groups:
        raise ValueError("groups.json has no interop section; rerun grouping report")
    section = groups["interop"]
    return section["status"], [PairResult.from_json(p) for p in section["pairs"]]


def failed_pairs(groups: dict) -> set[frozenset[str]]:
    return {r.members for r in section_results(groups)[1] if r.result == "fail"}


def pair_status(groups: dict, a: str, b: str) -> str:
    status, results = section_results(groups)
    if status == NOT_RUN:
        return NOT_RUN
    return next((r.result for r in results if r.members == frozenset((a, b))), NOT_PLANNED)
