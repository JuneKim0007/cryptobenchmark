from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Callable

from ....dto.prompt import Charter, TaskPrompt, ToolResultPrompt
from ....inputs.table import DEFAULT_CALLS, DEFAULT_SESSIONS, DEFAULT_TURNS
from ..agent import AgentRefused, Conversations
from .budget import fit, measure

TOOL_RESULT = "tool-result"


@dataclass(frozen=True)
class Answer:
    """What one reply came to: a decision, its problems, or a read tool's text the next turn carries."""
    decision: dict | None = None
    problems: tuple[str, ...] = ()
    result: str | None = None


Check = Callable[[str], "Answer | tuple[dict | None, list[str]]"]


@dataclass(frozen=True)
class Limits:
    turns: int = DEFAULT_TURNS
    sessions: int = DEFAULT_SESSIONS
    # read-tool calls one session may make before it must submit
    calls: int = DEFAULT_CALLS


@dataclass(frozen=True)
class Turn:
    session: int
    turn: int
    status: str            # accepted | rejected | refused | tool
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

    @property
    def answered(self) -> str | None:
        """The model the provider named on the last reply."""
        return next((t.reply.get("model") or None for t in reversed(self.turns) if t.reply), None)


def _answer(found) -> Answer:
    return found if isinstance(found, Answer) else Answer(found[0], tuple(found[1]))


def _status(answer: Answer) -> str:
    if answer.result is not None:
        return "tool"
    return "accepted" if answer.decision is not None and not answer.problems else "rejected"


def ask(conversations: Conversations, charter: Charter, message: TaskPrompt, check: Check, limits: Limits,
        on_turn: Callable[[Turn], None] = lambda _: None, narrow: Callable[[], TaskPrompt] | None = None) -> Asked:
    fitted = fit(getattr(conversations, "budget", None), charter.system, message, narrow)
    asked = Asked(narrowedFrom=fitted.narrowedFrom)
    for session in range(1, limits.sessions + 1):
        conversation, prompt = conversations.start(charter.system, charter.schema), fitted.message
        n, rejected, calls = 0, 0, 0
        while rejected < limits.turns:
            n += 1
            sha = hashlib.sha256(prompt.text.encode()).hexdigest()[:12]
            started, refusal = time.monotonic(), None
            try:
                reply = conversation.ask(prompt)
            except AgentRefused as e:
                refusal = e
            # the model's latency only; the gate's check is static and not counted
            elapsed = int((time.monotonic() - started) * 1000)
            if refusal is not None:
                answer, status, kept = Answer(None, (f"model refused: {refusal}",)), "refused", None
            else:
                answer, kept = _answer(check(reply.text)), reply.to_json()
                status = _status(answer)
            turn = Turn(session, n, status, answer.problems, kept, sha, elapsed, measure(charter.system, prompt))
            asked.turns.append(turn)
            on_turn(turn)
            if status == "accepted":
                asked.decision = answer.decision
                return asked
            if status == "refused":
                # a refusal can leave no session to correct (no session id on turn 1); the next session re-sends the task
                break
            if status == "tool" and calls < limits.calls:
                calls += 1
                prompt = ToolResultPrompt(TOOL_RESULT, answer.result)
                continue
            rejected += 1
            problems = list(answer.problems) or [f"{limits.calls} tool calls made; submit now"]
            prompt = charter.correct(problems)
    return asked
