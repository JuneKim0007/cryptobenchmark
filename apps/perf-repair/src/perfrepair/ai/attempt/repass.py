"""Repass: a fresh attempt on the same item with the reason the last one failed; at most MAX_REPASSES, then escalation."""
from __future__ import annotations

from dataclasses import dataclass

MAX_REPASSES = 2
# where a reason came from: the submit's checks, an attempt that never submitted, or the reviewer's refusal
CHECKS, NO_SUBMIT, REVIEW = "checks", "no_submit", "review"


@dataclass(frozen=True)
class Reason:
    source: str
    problems: tuple[str, ...]

    def to_json(self) -> dict:
        return {"source": self.source, "problems": list(self.problems)}

    def line(self) -> str:
        return f"{self.source}: " + "; ".join(self.problems)


@dataclass
class Repass:
    """The reasons of one tier's attempts; another repass while fewer than MAX_REPASSES were given."""
    reasons: list[Reason]

    def more(self) -> bool:
        return len(self.reasons) <= MAX_REPASSES

    def facts(self) -> list[str]:
        """What the next attempt's message carries: each earlier attempt's reason, oldest first."""
        return [f"attempt {n} was refused: {r.line()}" for n, r in enumerate(self.reasons, 1)]
