"""The one spawn handler: role → gateway → checked values → Conversations; every error comes before any work."""
from __future__ import annotations

import argparse
import os
from dataclasses import fields
from typing import Any, Callable

from ....config.load import Loaded
from ....config.settings import ConfigError
from ....dto.decision import AgentIdentity
from ....dto.prompt import SystemPrompt
from ....inputs.resolve import Candidate, choose, unknown_key
from ....inputs.table import AI_GATEWAY_AUTH, AI_GATEWAY_KEY, AI_GATEWAY_USE, RoleRow, Row
from ..agent.conversation import Conversation, Conversations
from ..engine.budget import Budget
from . import registry
from .contract import Gateway


class Spawned:
    """A gateway's Conversations plus what the engine records per outbox record and the role's budget it checks."""

    def __init__(self, conversations: Conversations, identity: AgentIdentity, budget: Budget | None = None):
        self.conversations, self.identity, self.budget = conversations, identity, budget

    def start(self, system: SystemPrompt, schema: dict) -> Conversation:
        return self.conversations.start(system, schema)


def _key_check(gateway: Gateway) -> Callable[[str, Any], None]:
    """One key against the gateway's settings class; a role key's name ends with it."""
    return lambda name, value: gateway.settings(**{name.rsplit(".", 1)[-1]: value})


def _row(key: str) -> Row:
    return AI_GATEWAY_AUTH if AI_GATEWAY_AUTH.key.endswith(f".{key}") else AI_GATEWAY_KEY


def _checked_blocks(settings: Loaded) -> dict[str, dict[str, Any]]:
    """Every block on each spawn; a bad value counts as unset at the block's layer, after its one warning."""
    origin, checked = f"file {settings.file}", {}
    for name, block in settings.settings.blocks.items():
        where = f"aiGateway.{name}"
        gateway = registry.gateway(name, where)
        keys = [f.name for f in fields(gateway.settings)]
        checked[name] = {}
        for key, value in block.items():
            if key not in keys:
                unknown_key(f"{where}.{key}", keys, origin)
            elif choose(f"{where}.{key}", [Candidate(value, origin)], _key_check(gateway), _row(key).invalid):
                checked[name][key] = value
    return checked


def _values(gateway: Gateway, role: RoleRow, cli: dict[str, Any], settings: Loaded, block: dict[str, Any]) -> Any:
    where = f"aiGateway.{gateway.name}"
    return gateway.settings(**{
        f.name: settings.role_value(role, f.name, _row(f.name), cli.get(f.name), (block.get(f.name), where), f.default,
                                    _key_check(gateway))
        for f in fields(gateway.settings)})


def spawn(args: argparse.Namespace, settings: Loaded, dry_run: Conversations) -> Spawned:
    """dry_run: the role's stand-in answers, for the gateway that answers without a model."""
    role = args.agent_role
    name = settings.role_value(role, "gateway", AI_GATEWAY_USE, args.agent, (settings.settings.get(AI_GATEWAY_USE.key), AI_GATEWAY_USE.key),
                               registry.DEFAULT, AI_GATEWAY_USE.check)
    gateway = registry.gateway(name, settings.sources[f"{role.key}.gateway"])
    blocks = _checked_blocks(settings)
    values = _values(gateway, role, {"auth": args.auth, "model": args.model, "effort": args.effort}, settings,
                     blocks.get(name, {}))
    secret = gateway.secret(values)
    if secret and not os.environ.get(secret):
        raise ConfigError(f"missing_secret: {secret}: gateway {name} needs it in the environment or .env")
    return Spawned(gateway.spawn(values, dry_run),
                   AgentIdentity(name, getattr(values, "model", None), getattr(values, "effort", None)),
                   Budget(role.budget_row.key, settings.read(role.budget_row)))
