from __future__ import annotations

import json
from typing import Callable, Protocol

from ...dto.prompt import CorrectionPrompt, SystemPrompt, TaskPrompt
from .claude import DEFAULT_MODEL, MAX_TOKENS, ClaudeClient
from .reply import AgentReply


class Conversation(Protocol):
    def ask(self, message: TaskPrompt | CorrectionPrompt) -> AgentReply: ...


class Conversations(Protocol):
    def start(self, system: SystemPrompt, schema: dict) -> Conversation: ...


class ClaudeConversation:

    def __init__(self, client: ClaudeClient, system: SystemPrompt, schema: dict):
        self.client, self.system, self.schema, self.messages = client, system, schema, []

    def ask(self, message: TaskPrompt | CorrectionPrompt) -> AgentReply:
        self.messages.append({"role": "user", "content": message.text})
        reply, content = self.client.request(self.system.text, self.messages, self.schema)
        # The whole content goes back, thinking blocks included: the API checks them on the next turn.
        self.messages.append({"role": "assistant", "content": content})
        return reply


class ClaudeConversations:

    def __init__(self, model: str = DEFAULT_MODEL, effort: str = "medium", max_tokens: int = MAX_TOKENS, client=None):
        self.client = ClaudeClient(model, effort, max_tokens, client)

    def start(self, system: SystemPrompt, schema: dict) -> ClaudeConversation:
        return ClaudeConversation(self.client, system, schema)


class ScriptedConversations:

    def __init__(self, answer: Callable[[TaskPrompt, int, int], dict | str]):
        self.answer, self.started, self.turns, self.systems = answer, 0, [], []

    def start(self, system: SystemPrompt, schema: dict) -> "_Scripted":
        self.started += 1
        self.systems.append(system)
        return _Scripted(self, self.started)


class _Scripted:

    def __init__(self, owner: ScriptedConversations, number: int):
        self.owner, self.number, self.turn, self.task = owner, number, 0, None

    def ask(self, message: TaskPrompt | CorrectionPrompt) -> AgentReply:
        self.turn += 1
        self.task = self.task or message
        self.owner.turns.append((self.number, self.turn, message))
        out = self.owner.answer(self.task, self.number, self.turn)
        return AgentReply(out if isinstance(out, str) else json.dumps(out), "scripted")
