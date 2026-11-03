"""A candidate's pair diff against a scope's current item and the change class it implies, or why it is rejected."""
from __future__ import annotations

from dataclasses import asdict, dataclass

DROP_IN, LOCAL_EDIT, MIGRATION = "drop-in", "local-edit", "migration"
# in rank order: a maxChange admits its own class and every one before it
CHANGES = (DROP_IN, LOCAL_EDIT, MIGRATION)
REJECTED = "rejected"
CLASSES = (*CHANGES, REJECTED)
SAME = "same"
INPUT_DIFFS = (SAME, "reshaped", "new_parameter")
KEY_DIFFS = (SAME, "size", "type")
OUTPUT_DIFFS = (SAME, "bytes", "kind")
# persist: the output is stored, sent, or goes where code cannot see
REACHES = ("local", "return", "persist")
REJECT_REASONS = ("type_unknown", "strength_below", "strength_unknown", "authenticated_lost", "deterministic_lost",
                  "nonce_not_generated", "unavailable", "availability_unknown", "not_measured", "deprecated")


def admits(max_change: str, change: str) -> bool:
    return change in CHANGES and CHANGES.index(change) <= CHANGES.index(max_change)


@dataclass(frozen=True)
class PairDiff:
    input: str
    key: str
    output: str
    reach: str

    @classmethod
    def same(cls, reach: str) -> "PairDiff":
        return cls(SAME, SAME, SAME, reach)


@dataclass(frozen=True)
class Change:
    """change: one of CLASSES; reasons: every reject reason found, empty unless rejected."""
    item: str
    change: str
    diff: PairDiff
    reasons: tuple[str, ...] = ()

    def to_json(self) -> dict:
        return {"item": self.item, "change": self.change, "diff": asdict(self.diff), "reasons": list(self.reasons)}

    @classmethod
    def from_json(cls, d: dict) -> "Change":
        return cls(d["item"], d["change"], PairDiff(**d["diff"]), tuple(d["reasons"]))
