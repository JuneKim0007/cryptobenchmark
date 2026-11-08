from __future__ import annotations

import json
from typing import Callable, Protocol

from ....dto.prompt import CorrectionPrompt, SystemPrompt, TaskPrompt, ToolResultPrompt
from .reply import AgentReply


class Conversation(Protocol):
    def ask(self, message: TaskPrompt | CorrectionPrompt | ToolResultPrompt) -> AgentReply: ...


class Conversations(Protocol):
    def start(self, system: SystemPrompt, schema: dict) -> Conversation: ...


class LifetimeGuarded:
    """Every gateway's conversation: a SystemPrompt, then one TaskPrompt, then only corrections and tool results."""

    def __init__(self, system: SystemPrompt):
        if not isinstance(system, SystemPrompt):
            raise TypeError(f"lifetime_mismatch: a conversation starts with a SystemPrompt, not {type(system).__name__}")
        self.system, self.task = system, None

    def ask(self, message: TaskPrompt | CorrectionPrompt | ToolResultPrompt) -> AgentReply:
        expected = (CorrectionPrompt, ToolResultPrompt) if self.task else (TaskPrompt,)
        if not isinstance(message, expected):
            raise TypeError(f"lifetime_mismatch: {'after the task' if self.task else 'the first turn'} takes a "
                            f"{' or '.join(e.__name__ for e in expected)}, not {type(message).__name__}")
        self.task = self.task or message
        return self._send(message)

    def _send(self, message: TaskPrompt | CorrectionPrompt) -> AgentReply:
        raise NotImplementedError


class ScriptedConversations:

    def __init__(self, answer: Callable[[TaskPrompt, int, int], dict | str]):
        self.answer, self.started, self.turns, self.systems = answer, 0, [], []

    def start(self, system: SystemPrompt, schema: dict) -> "_Scripted":
        self.started += 1
        self.systems.append(system)
        return _Scripted(self, system, self.started)


class _Scripted(LifetimeGuarded):

    def __init__(self, owner: ScriptedConversations, system: SystemPrompt, number: int):
        super().__init__(system)
        self.owner, self.number, self.turn = owner, number, 0

    def _send(self, message: TaskPrompt | CorrectionPrompt) -> AgentReply:
        self.turn += 1
        self.owner.turns.append((self.number, self.turn, message))
        out = self.owner.answer(self.task, self.number, self.turn)
        return AgentReply(out if isinstance(out, str) else json.dumps(out), "scripted")
