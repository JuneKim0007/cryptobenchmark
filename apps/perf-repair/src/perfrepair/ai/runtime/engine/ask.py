from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Callable

from ....dto.prompt import Charter, TaskPrompt
from ....inputs.table import DEFAULT_SESSIONS, DEFAULT_TURNS
from ..agent import AgentRefused, Conversations
from .budget import fit, measure

Check = Callable[[str], tuple[dict | None, list[str]]]


@dataclass(frozen=True)
class Limits:
    turns: int = DEFAULT_TURNS
    sessions: int = DEFAULT_SESSIONS


@dataclass(frozen=True)
class Turn:
    session: int
    turn: int
    status: str            # accepted | rejected | refused
    problems: tuple[str, ...]
    reply: dict | None
    messageSha: str
    durationMs: int = 0
    promptTokens: int = 0

    def to_json(self) -> dict:
        return {"session": self.session, "turn": self.turn, "status": self.status, "problems": list(self.problems),
                "reply": self.reply, "messageSha": self.messageSha, "durationMs": self.durationMs,
                "promptTokens": self.promptTokens}


@dataclass
class Asked:
    decision: dict | None = None
    turns: list[Turn] = field(default_factory=list)
    narrowedFrom: int | None = None

    @property
    def last(self) -> Turn:
        return self.turns[-1]

    @property
    def problems(self) -> list[str]:
        return [f"s{t.session}t{t.turn}: {p}" for t in self.turns for p in t.problems]


def ask(conversations: Conversations, charter: Charter, message: TaskPrompt, check: Check, limits: Limits,
        on_turn: Callable[[Turn], None] = lambda _: None, narrow: Callable[[], TaskPrompt] | None = None) -> Asked:
    fitted = fit(getattr(conversations, "budget", None), charter.system, message, narrow)
    asked = Asked(narrowedFrom=fitted.narrowedFrom)
    for session in range(1, limits.sessions + 1):
        conversation, prompt = conversations.start(charter.system, charter.schema), fitted.message
        for n in range(1, limits.turns + 1):
            sha = hashlib.sha256(prompt.text.encode()).hexdigest()[:12]
            started, refusal = time.monotonic(), None
            try:
                reply = conversation.ask(prompt)
            except AgentRefused as e:
                refusal = e
            # the model's latency only; the gate's check is static and not counted
            elapsed = int((time.monotonic() - started) * 1000)
            if refusal is not None:
                decision, problems, status, kept = None, [f"model refused: {refusal}"], "refused", None
            else:
                decision, problems = check(reply.text)
                status = "accepted" if decision is not None and not problems else "rejected"
                kept = reply.to_json()
            turn = Turn(session, n, status, tuple(problems), kept, sha, elapsed, measure(charter.system, prompt))
            asked.turns.append(turn)
            on_turn(turn)
            if status == "accepted":
                asked.decision = decision
                return asked
            if status == "refused":
                # a refusal can leave no session to correct (no session id on turn 1); the next session re-sends the task
                break
            prompt = charter.correct(problems)
    return asked
