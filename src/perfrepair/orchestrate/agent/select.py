"""--agent on every command: the backend name → an Agent (single call) or Conversations (multi-turn)."""
from __future__ import annotations

from .claude import ClaudeAgent
from .claude_code import ClaudeCodeAgent, ClaudeCodeConversations
from .conversation import ClaudeConversations

BACKENDS = ("claude", "claude-code", "dry-run")


def conversations(name: str, model: str, effort: str, dry_run):
    """dry_run: the Conversations the command uses when no model is called."""
    if name == "claude":
        return ClaudeConversations(model, effort)
    if name == "claude-code":
        return ClaudeCodeConversations(model, effort)
    return dry_run


def agent(name: str, model: str, effort: str, dry_run):
    if name == "claude":
        return ClaudeAgent(model, effort)
    if name == "claude-code":
        return ClaudeCodeAgent(model, effort)
    return dry_run
