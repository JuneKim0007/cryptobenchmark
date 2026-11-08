from __future__ import annotations

from dataclasses import dataclass

from ....config.timeouts import claude_seconds
from ....inputs.check import check_bool, check_one_of, check_text
from ...model.tier import Ladder
from ..agent.conversation import Conversations
from .claude_api import DEFAULT_MODEL, ClaudeConversations
from .claude_cli import ClaudeCliConversations
from .contract import Gateway

AUTHS = ("subscription", "api")
EFFORTS = ("low", "medium", "high", "xhigh", "max")
# weakest first: escalation's next model
MODELS = ("claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5")
API_KEY = "ANTHROPIC_API_KEY"


@dataclass(frozen=True)
class ClaudeSettings:
    auth: str = "subscription"
    model: str = DEFAULT_MODEL
    effort: str = "medium"
    binary: str = "claude"
    webSearch: bool = False

    def __post_init__(self):
        check_one_of("auth", self.auth, AUTHS)
        check_text("model", self.model)
        check_one_of("effort", self.effort, EFFORTS)
        check_text("binary", self.binary)
        check_bool("webSearch", self.webSearch)


def _secret(values: ClaudeSettings) -> str | None:
    return API_KEY if values.auth == "api" else None


def _spawn(values: ClaudeSettings, _dry_run: Conversations) -> Conversations:
    if values.auth == "api":
        return ClaudeConversations(values.model, values.effort, web_search=values.webSearch)
    return ClaudeCliConversations(values.model, values.effort, binary=values.binary, timeout=claude_seconds(),
                                  web_search=values.webSearch)


GATEWAY = Gateway("claude", ClaudeSettings, _spawn, _secret, {"auth": AUTHS, "effort": EFFORTS}, Ladder(MODELS))
