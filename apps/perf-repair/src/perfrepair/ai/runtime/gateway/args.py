"""--agent, --auth, --model, --effort on every model command, with each role's default in the help."""
from __future__ import annotations

import argparse

from ....config.args import add_config_arg
from ....config.load import GATEWAY_ENV
from ....inputs.table import ROLE_KEYS, RoleRow
from . import registry


def _choices(key: str) -> str:
    known = [f"{g.name}: {', '.join(g.choices[key])}" for g in registry.GATEWAYS.values() if key in g.choices]
    return f"; {'; '.join(known)}" if known else ""


def _default(role: RoleRow, key: str) -> str:
    fallback = role.defaults.get(key) or getattr(registry.GATEWAYS[registry.DEFAULT].settings(), key)
    section = f"{role.key}.{key} in perfrepair.yaml, " if key in ROLE_KEYS else ""
    return f"default: {section}${GATEWAY_ENV[key]}, aiGateway.<use>.{key}, else {fallback}{_choices(key)}"


def add_agent_args(parser: argparse.ArgumentParser, role: RoleRow) -> None:
    """Unset flags resolve per role in `spawn` (docs/settings.md)."""
    parser.add_argument("--agent", choices=list(registry.GATEWAYS),
                        help=f"the gateway; default: {role.key}.gateway in perfrepair.yaml, ${GATEWAY_ENV['gateway']}, "
                             f"aiGateway.use, else {registry.DEFAULT}")
    parser.add_argument("--auth", help=_default(role, "auth"))
    parser.add_argument("--model", help=_default(role, "model"))
    parser.add_argument("--effort", help=_default(role, "effort"))
    add_config_arg(parser)
    parser.set_defaults(agent_role=role)
