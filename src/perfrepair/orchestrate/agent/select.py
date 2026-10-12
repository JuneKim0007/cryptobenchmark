from __future__ import annotations

import argparse
import os

from .claude import DEFAULT_MODEL
from .claude_code import ClaudeCodeConversations
from .conversation import ClaudeConversations
from ...env import load_env

BACKENDS = ("claude", "claude-code", "dry-run")
EFFORTS = ("low", "medium", "high", "xhigh", "max")


def add_agent_args(parser: argparse.ArgumentParser, effort: str = "medium") -> None:
    """Defaults come from PERFREPAIR_AGENT / _MODEL / _EFFORT (.env), then from here."""
    load_env()
    parser.add_argument("--agent", choices=BACKENDS, default=os.environ.get("PERFREPAIR_AGENT", "claude-code"))
    parser.add_argument("--model", default=os.environ.get("PERFREPAIR_MODEL", DEFAULT_MODEL))
    parser.add_argument("--effort", default=os.environ.get("PERFREPAIR_EFFORT", effort), choices=EFFORTS)


def conversations(args: argparse.Namespace, dry_run):
    if args.agent == "claude":
        return ClaudeConversations(args.model, args.effort)
    if args.agent == "claude-code":
        return ClaudeCodeConversations(args.model, args.effort)
    return dry_run
