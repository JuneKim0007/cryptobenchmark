from __future__ import annotations

from dataclasses import dataclass

from ....inputs.check import check_one_of, check_text
from ..agent.conversation import Conversations
from .claude_api import DEFAULT_MODEL, ClaudeConversations
from .claude_cli import ClaudeCliConversations
from .contract import Gateway

AUTHS = ("subscription", "api")
EFFORTS = ("low", "medium", "high", "xhigh", "max")
API_KEY = "ANTHROPIC_API_KEY"


@dataclass(frozen=True)
class ClaudeSettings:
    auth: str = "subscription"
    model: str = DEFAULT_MODEL
    effort: str = "medium"
    binary: str = "claude"

    def __post_init__(self):
        check_one_of("auth", self.auth, AUTHS)
        check_text("model", self.model)
        check_one_of("effort", self.effort, EFFORTS)
        check_text("binary", self.binary)


def _secret(values: ClaudeSettings) -> str | None:
    return API_KEY if values.auth == "api" else None


def _spawn(values: ClaudeSettings, _dry_run: Conversations) -> Conversations:
    if values.auth == "api":
        return ClaudeConversations(values.model, values.effort)
    return ClaudeCliConversations(values.model, values.effort, binary=values.binary)


GATEWAY = Gateway("claude", ClaudeSettings, _spawn, _secret, {"auth": AUTHS, "effort": EFFORTS})
