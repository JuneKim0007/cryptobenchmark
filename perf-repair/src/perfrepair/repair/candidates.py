"""An app's call sites joined to the grouping: the item each site runs and the runnable members that could replace it."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from ..dto.grouping import qualified

RESOLVED = ("default", "explicit")


@dataclass(frozen=True)
class Candidate:
    file: str
    line: int
    snippet: str
    engineType: str
    algorithm: str | None
    provider: str | None
    item: str
    group: str | None
    alternatives: tuple[str, ...]

    def to_json(self) -> dict:
        return asdict(self) | {"alternatives": list(self.alternatives)}

    @classmethod
    def from_json(cls, d: dict) -> "Candidate":
        return cls(**{**d, "alternatives": tuple(d["alternatives"])})


def candidates(sites_doc: dict, groups_doc: dict) -> list[Candidate]:
    by_qualified = {v["qualified"]: key for key, v in groups_doc["items"].items()}
    runnable = {g["id"]: [str(m) for m in g["runnable"]] for g in groups_doc["groups"]}
    out = []
    for s in sites_doc["sites"]:
        if s["resolution"] not in RESOLVED:
            continue
        item = by_qualified.get(qualified(s["engineType"], s["resolvedAlgorithm"], s["resolvedProvider"]))
        if item is None:
            continue
        group = groups_doc["items"][item]["group"]
        out.append(Candidate(s["file"], s["line"], s["snippet"], s["engineType"], s["algorithm"]["literal"],
                             (s.get("provider") or {}).get("literal"), item, group,
                             tuple(m for m in runnable.get(group, []) if m != item)))
    return out
