"""What an agent is: one stateless call `(system, user, schema) -> AgentReply`, nothing remembered."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class AgentReply:
    text: str
    model: str = ""
    requestId: str = ""
    usage: dict = field(default_factory=dict)


class AgentRefused(RuntimeError):
    """The model declined the request (stop_reason "refusal")."""


class Agent(Protocol):
    def __call__(self, system: str, user: str, schema: dict) -> AgentReply: ...
