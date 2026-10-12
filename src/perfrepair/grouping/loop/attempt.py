"""One conversation's turns for one item: ask, gate the answer, and on rejection ask again in the same
conversation with the problems listed, up to a turn limit."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Callable

from ...dto.grouping_state import Answer
from ...orchestrate.agent import AgentRefused, Conversation
from ..prompt.render import rejection

Check = Callable[[str], tuple[Answer | None, list[str]]]


@dataclass(frozen=True)
class Turn:
    session: int
    turn: int
    status: str            # accepted | rejected | refused
    problems: tuple[str, ...]
    reply: dict | None
    messageSha: str


@dataclass
class Attempt:
    answer: Answer | None = None
    turns: list[Turn] = field(default_factory=list)


def attempt(conversation: Conversation, message: str, check: Check, turns: int, session: int) -> Attempt:
    result = Attempt()
    for n in range(1, turns + 1):
        sha = hashlib.sha256(message.encode()).hexdigest()[:12]
        try:
            reply = conversation.ask(message)
        except AgentRefused as e:
            answer, problems, status, kept = None, [f"model refused: {e}"], "refused", None
        else:
            answer, problems = check(reply.text)
            status = "accepted" if answer is not None and not problems else "rejected"
            kept = {"text": reply.text, "model": reply.model, "requestId": reply.requestId, "usage": reply.usage}
        result.turns.append(Turn(session, n, status, tuple(problems), kept, sha))
        if status == "accepted":
            result.answer = answer
            return result
        message = rejection(problems)
    return result
