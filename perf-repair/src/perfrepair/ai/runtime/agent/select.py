from __future__ import annotations

import argparse

from ....config.args import add_config_arg
from ....config.load import AGENT_ENV, Loaded
from ....config.settings import AGENT_DEFAULT, BACKENDS, EFFORTS, ROLE_DEFAULTS, ROLES, Agent
from ..gateway.claude_api import ClaudeConversations
from ..gateway.claude_cli import ClaudeCliConversations


def _default(role: str, name: str) -> str:
    own = getattr(ROLE_DEFAULTS.get(role, Agent()), name) or getattr(AGENT_DEFAULT, name)
    return f"default: {ROLES[role]}.{name} in perfrepair.yaml, ${AGENT_ENV[name]}, agent.{name}, else {own}"


def add_agent_args(parser: argparse.ArgumentParser, role: str) -> None:
    """Unset flags resolve per role in `conversations` (docs/settings.md)."""
    parser.add_argument("--agent", choices=BACKENDS, help=_default(role, "backend"))
    parser.add_argument("--model", help=_default(role, "model"))
    parser.add_argument("--effort", choices=EFFORTS, help=_default(role, "effort"))
    add_config_arg(parser)
    parser.set_defaults(agent_role=role)


def conversations(args: argparse.Namespace, settings: Loaded, dry_run):
    a = settings.agent(args.agent_role, {"backend": args.agent, "model": args.model, "effort": args.effort})
    if a.backend == "claude":
        return ClaudeConversations(a.model, a.effort)
    if a.backend == "claude-code":
        return ClaudeCliConversations(a.model, a.effort, binary=a.claudeBinary)
    return dry_run
