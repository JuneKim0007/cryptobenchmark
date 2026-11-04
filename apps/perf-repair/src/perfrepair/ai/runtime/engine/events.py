"""The engine's events: each model turn and each committed decision, pointing to the journal line or outbox record."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ....dto.event import DECISION, TURN
from ....log import emit
from .ask import Asked, Turn

TOKEN_KEYS = ("input", "output", "cacheRead", "cacheWrite")


@dataclass(frozen=True)
class Where:
    """Which stage and step a role's turns belong to, and the app folder when it has one."""
    stage: str
    step: str
    app: str | None = None


def tokens(turns: list[Turn]) -> dict | None:
    usages = [t.reply.get("usage") or {} for t in turns if t.reply]
    if not any(usages):
        return None
    return {k: sum(int(u.get(k) or 0) for u in usages) for k in TOKEN_KEYS}


def cost(turns: list[Turn]) -> float | None:
    costs = [(t.reply.get("usage") or {}).get("costUsd") for t in turns if t.reply]
    costs = [c for c in costs if c is not None]
    return round(sum(costs), 6) if costs else None


class TurnEvents:
    """Journal lines are counted, so each turn's event names the line that holds its reply."""

    def __init__(self, where: Where, journal: Path, line: int, fingerprint: str):
        self.where, self.journal, self.line, self.fingerprint = where, Path(journal), line, fingerprint

    def turn(self, item: str, turn: Turn) -> None:
        self.line += 1
        w = self.where
        emit(w.stage, w.step, TURN, kind="model", item=item, app=w.app, outcome=turn.status,
             durationMs=turn.durationMs, tokens=tokens([turn]), costUsd=cost([turn]), ref=f"{self.journal}:{self.line}",
             data={"session": turn.session, "turn": turn.turn, "problems": list(turn.problems),
                   "outbox": self.fingerprint})

    def decision(self, item: str, label: str, outcome: str, asked: Asked, ref: Path | None) -> None:
        w = self.where
        emit(w.stage, w.step, DECISION, kind="model", item=item, app=w.app, outcome=outcome,
             durationMs=sum(t.durationMs for t in asked.turns), tokens=tokens(asked.turns), costUsd=cost(asked.turns),
             ref=None if ref is None else str(ref),
             data={"label": label, "turns": len(asked.turns), "sessions": asked.last.session, "problems": asked.problems,
                   "outbox": self.fingerprint})
