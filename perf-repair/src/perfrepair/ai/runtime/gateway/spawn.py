"""The one spawn handler: role → gateway → checked values → Conversations; every error comes before any work."""
from __future__ import annotations

import argparse
import os
from dataclasses import fields
from typing import Any

from ....config.load import Loaded
from ....config.settings import ConfigError, Invalid
from ....dto.decision import AgentIdentity
from ....dto.prompt import SystemPrompt
from ..agent.conversation import Conversation, Conversations
from . import registry
from .contract import Gateway


class Spawned:
    """A gateway's Conversations plus what the engine records per outbox record."""

    def __init__(self, conversations: Conversations, identity: AgentIdentity):
        self.conversations, self.identity = conversations, identity

    def start(self, system: SystemPrompt, schema: dict) -> Conversation:
        return self.conversations.start(system, schema)


def _check_blocks(settings: Loaded) -> None:
    for name, block in settings.settings.aiGateway.blocks.items():
        where = f"aiGateway.{name}"
        keys = [f.name for f in fields(registry.gateway(name, where).settings)]
        unknown = sorted(str(k) for k in block if k not in keys)
        if unknown:
            raise ConfigError(f"unknown_keys: {where} {unknown}, known {keys} ({settings.file})")
        try:
            registry.gateway(name, where).settings(**block)
        except Invalid as e:
            raise ConfigError(f"invalid: {where}.{e.name} {e.value}, {e.expected} ({settings.file})") from None


def _values(gateway: Gateway, role: str, cli: dict[str, Any], settings: Loaded) -> Any:
    defaults = {f.name: f.default for f in fields(gateway.settings)}
    try:
        return gateway.settings(**settings.gateway_values(role, gateway.name, defaults, cli))
    except Invalid as e:
        raise ConfigError(f"invalid: {role}.{e.name} {e.value}, {e.expected} ({settings.sources[f'{role}.{e.name}']})") from None


def spawn(args: argparse.Namespace, settings: Loaded, dry_run: Conversations) -> Spawned:
    """dry_run: the role's stand-in answers, for the gateway that answers without a model."""
    role = args.agent_role
    name = settings.gateway_name(role, args.agent, registry.DEFAULT)
    gateway = registry.gateway(name, settings.sources[f"{role}.gateway"])
    _check_blocks(settings)
    values = _values(gateway, role, {"auth": args.auth, "model": args.model, "effort": args.effort}, settings)
    secret = gateway.secret(values)
    if secret and not os.environ.get(secret):
        raise ConfigError(f"missing_secret: {secret}: gateway {name} needs it in the environment or .env")
    return Spawned(gateway.spawn(values, dry_run),
                   AgentIdentity(name, getattr(values, "model", None), getattr(values, "effort", None)))
