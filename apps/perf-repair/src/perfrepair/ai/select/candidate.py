"""What Select chooses among: code's candidates for one item, each the whole swap it would make, and the item itself."""
from __future__ import annotations

from dataclasses import dataclass

from ...dto.dossier import Dossier, Option

REPLACE, RECOMMEND, UPGRADE = "replace", "recommend", "upgrade"
NONE = "none"


@dataclass(frozen=True)
class Pick:
    """One member's swap: its option and the risks code derives for it."""
    member: str
    dossier: Dossier
    option: Option
    risks: tuple[str, ...]


@dataclass(frozen=True)
class Candidate:
    alias: str
    item: str
    # replace: code applies it; recommend: a person must make what reads the output follow; upgrade: off a broken use
    decision: str
    picks: tuple[Pick, ...] = ()
    needs: tuple[str, ...] = ()
    option: Option | None = None


@dataclass(frozen=True)
class SelectItem:
    key: str
    label: str
    candidates: tuple[Candidate, ...]
    none_allowed: bool
    evidence: str
    text: str
    source: object

    def by_alias(self) -> dict[str, Candidate]:
        return {c.alias: c for c in self.candidates}

    def answers(self) -> list[str]:
        return [*self.by_alias(), *([NONE] if self.none_allowed else [])]
