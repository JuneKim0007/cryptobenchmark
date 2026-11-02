"""name → Gateway; a new provider is one module and one row here."""
from __future__ import annotations

from ....config.settings import ConfigError
from . import claude, dry_run
from .contract import Gateway

GATEWAYS = {g.name: g for g in (claude.GATEWAY, dry_run.GATEWAY)}
DEFAULT = claude.GATEWAY.name


def gateway(name: str, where: str) -> Gateway:
    if name not in GATEWAYS:
        raise ConfigError(f"unknown_gateway: {name} ({where}), known {list(GATEWAYS)}")
    return GATEWAYS[name]
