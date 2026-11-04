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
# unknown: a field takes the object or the output, or a sink is unknown; persist: the output is stored or sent
REACHES = ("local", "return", "unknown", "persist")
NO_GAIN = "no_gain"
# another spelling of the current item's canonical name from its own provider: one engine, nothing to measure
SAME_ENGINE = "same_engine"
REJECT_REASONS = ("type_unknown", "strength_below", "strength_unknown", "authenticated_lost", "deterministic_lost",
                  "nonce_not_generated", "unavailable", "availability_unknown", "not_measured", "deprecated", NO_GAIN,
                  SAME_ENGINE)


# facts a person checks before a recommendation is applied; never a verdict that it is fine
REACH_REVIEW = {"local": "reach_local_unverified", "return": "reach_return_unverified", "unknown": "reach_unknown",
                "persist": "reach_persist"}
FIELD_BOUND = "field_bound"
NEEDS_REVIEW = (*REACH_REVIEW.values(), FIELD_BOUND, "output_length_changes", "key_changes", "key_size_unknown",
                "parameter_changes", "adds_dependency", "resolved_by_order")


# provider_path: the same canonical name from another provider the app has; the only kind a swap can be applied as
PROVIDER_PATH, RECOMMENDATION = "provider_path", "recommendation"
TRACKS = (PROVIDER_PATH, RECOMMENDATION)


def output_changes(diff: "PairDiff | None") -> bool:
    return diff is not None and diff.output != SAME


def admits(max_change: str, change: str) -> bool:
    return change in CHANGES and CHANGES.index(change) <= CHANGES.index(max_change)


@dataclass(frozen=True)
class PairDiff:
    input: str
    key: str
    output: str
    reach: str
    # the candidate's provider is one the harness installed and the app does not ship
    addsDependency: bool = False

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
        return {"item": self.item, "change": self.change, "diff": asdict(self.diff), "reasons": list(self.reasons),
                "outputChanges": output_changes(self.diff)}

    @classmethod
    def from_json(cls, d: dict) -> "Change":
        return cls(d["item"], d["change"], PairDiff(**d["diff"]), tuple(d["reasons"]))
