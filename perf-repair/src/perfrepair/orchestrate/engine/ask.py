from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Callable

from ...dto.prompt import Charter, TaskPrompt
from ..agent import AgentRefused, Conversations

Check = Callable[[str], tuple[dict | None, list[str]]]


@dataclass(frozen=True)
class Limits:
    turns: int = 3
    sessions: int = 2


@dataclass(frozen=True)
class Turn:
    session: int
    turn: int
    status: str            # accepted | rejected | refused
    problems: tuple[str, ...]
    reply: dict | None
    messageSha: str

    def to_json(self) -> dict:
        return {"session": self.session, "turn": self.turn, "status": self.status, "problems": list(self.problems),
                "reply": self.reply, "messageSha": self.messageSha}


@dataclass
class Asked:
    decision: dict | None = None
    turns: list[Turn] = field(default_factory=list)

    @property
    def last(self) -> Turn:
        return self.turns[-1]

    @property
    def problems(self) -> list[str]:
        return [f"s{t.session}t{t.turn}: {p}" for t in self.turns for p in t.problems]


def ask(conversations: Conversations, charter: Charter, message: TaskPrompt, check: Check, limits: Limits,
        on_turn: Callable[[Turn], None] = lambda _: None) -> Asked:
    if not isinstance(message, TaskPrompt):
        raise TypeError(f"lifetime_mismatch: a session opens with a TaskPrompt, not {type(message).__name__}")
    asked = Asked()
    for session in range(1, limits.sessions + 1):
        conversation, prompt = conversations.start(charter.system, charter.schema), message
        for n in range(1, limits.turns + 1):
            sha = hashlib.sha256(prompt.text.encode()).hexdigest()[:12]
            try:
                reply = conversation.ask(prompt)
            except AgentRefused as e:
                decision, problems, status, kept = None, [f"model refused: {e}"], "refused", None
            else:
                decision, problems = check(reply.text)
                status = "accepted" if decision is not None and not problems else "rejected"
                kept = reply.to_json()
            turn = Turn(session, n, status, tuple(problems), kept, sha)
            asked.turns.append(turn)
            on_turn(turn)
            if status == "accepted":
                asked.decision = decision
                return asked
            prompt = charter.correct(problems)
    return asked
