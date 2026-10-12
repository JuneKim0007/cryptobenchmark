"""A conversation: several turns with one agent, its history kept inside; a new one starts with none.

The grouping loop asks again in the same conversation when an answer is rejected, and starts a new one
to respawn; Conversations is the factory it is given, so it never knows whether a model is real.
"""
from __future__ import annotations

import json
from typing import Callable, Protocol

from .claude import DEFAULT_MODEL, MAX_TOKENS, ClaudeClient
from .reply import AgentReply


class Conversation(Protocol):
    def ask(self, user: str) -> AgentReply: ...


class Conversations(Protocol):
    def start(self, system: str, schema: dict) -> Conversation: ...


class ClaudeConversation:

    def __init__(self, client: ClaudeClient, system: str, schema: dict):
        self.client, self.system, self.schema, self.messages = client, system, schema, []

    def ask(self, user: str) -> AgentReply:
        self.messages.append({"role": "user", "content": user})
        reply, content = self.client.request(self.system, self.messages, self.schema)
        # The whole content goes back, thinking blocks included: the API checks them on the next turn.
        self.messages.append({"role": "assistant", "content": content})
        return reply


class ClaudeConversations:

    def __init__(self, model: str = DEFAULT_MODEL, effort: str = "medium", max_tokens: int = MAX_TOKENS, client=None):
        self.client = ClaudeClient(model, effort, max_tokens, client)

    def start(self, system: str, schema: dict) -> ClaudeConversation:
        return ClaudeConversation(self.client, system, schema)


class ScriptedConversations:
    """Tests and dry runs: replies from `answer(user message, conversation number, turn)`; every turn recorded."""

    def __init__(self, answer: Callable[[str, int, int], dict | str]):
        self.answer, self.started, self.turns = answer, 0, []

    def start(self, system: str, schema: dict) -> "_Scripted":
        self.started += 1
        return _Scripted(self, self.started)


class _Scripted:

    def __init__(self, owner: ScriptedConversations, number: int):
        self.owner, self.number, self.turn = owner, number, 0

    def ask(self, user: str) -> AgentReply:
        self.turn += 1
        self.owner.turns.append((self.number, self.turn, user))
        out = self.owner.answer(user, self.number, self.turn)
        return AgentReply(out if isinstance(out, str) else json.dumps(out), "scripted")
