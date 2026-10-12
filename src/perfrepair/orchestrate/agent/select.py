"""--agent on every command: the backend name → Conversations, and the arguments every stage shares."""
from __future__ import annotations

import argparse

from .claude import DEFAULT_MODEL
from .claude_code import ClaudeCodeConversations
from .conversation import ClaudeConversations

BACKENDS = ("claude", "claude-code", "dry-run")
EFFORTS = ("low", "medium", "high", "xhigh", "max")


def add_agent_args(parser: argparse.ArgumentParser, effort: str = "medium") -> None:
    parser.add_argument("--agent", choices=BACKENDS, default="claude")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--effort", default=effort, choices=EFFORTS)


def conversations(args: argparse.Namespace, dry_run):
    """dry_run: the Conversations the command uses when no model is called."""
    if args.agent == "claude":
        return ClaudeConversations(args.model, args.effort)
    if args.agent == "claude-code":
        return ClaudeCodeConversations(args.model, args.effort)
    return dry_run
