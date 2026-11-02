"""Finds perfrepair.yaml and resolves each value: CLI > environment > file > .env > code default, recording its source."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Mapping

import yaml

from ..files import read_yaml
from .dotenv import ROOT
from .settings import AGENT_DEFAULT, ROLE_DEFAULTS, ROLES, Agent, ConfigError, Invalid, Settings, parse

LOG = logging.getLogger(__name__)
DEFAULT_FILE = ROOT / "perfrepair.yaml"
CONFIG_ENV = "PERFREPAIR_CONFIG"
AGENT_ENV = {"backend": "PERFREPAIR_AGENT", "model": "PERFREPAIR_MODEL", "effort": "PERFREPAIR_EFFORT"}


def config_file(argument: Path | None, environ: Mapping[str, str]) -> Path | None:
    for path, origin in ((argument, "--perfrepair-config"), (environ.get(CONFIG_ENV), CONFIG_ENV)):
        if path:
            if not Path(path).expanduser().is_file():
                raise ConfigError(f"missing_file: {path} ({origin})")
            return Path(path).expanduser().resolve()
    return DEFAULT_FILE if DEFAULT_FILE.is_file() else None


def _agent_layer(values: Mapping[str, str], origin: str) -> Agent:
    layer = {name: values.get(var) or None for name, var in AGENT_ENV.items()}
    try:
        return Agent(**layer)
    except Invalid as e:
        raise ConfigError(f"invalid: {origin}{AGENT_ENV[e.name]} {e.value}, {e.expected}") from None


@dataclass
class Loaded:
    file: Path | None
    settings: Settings
    environ: Agent
    dotenv: Agent
    sources: dict[str, str] = field(default_factory=dict)

    def _pick(self, key: str, candidates) -> Any:
        value, source = next(((v, s) for v, s in candidates if v is not None), (None, "default"))
        if key not in self.sources:
            # shown: what a file or the environment chose; the rest stays in the log
            quiet = source == "cli" or source.startswith("default")
            LOG.log(logging.DEBUG if quiet else logging.INFO, "setting %s: %s (%s)", key, value, source)
        self.sources[key] = source
        return value

    def value(self, key: str, cli: Any = None, default: Any = None) -> Any:
        return self._pick(key, ((cli, "cli"), (self.settings.get(key), f"file {self.file}"), (default, "default")))

    def agent(self, role: str, cli: Mapping[str, Any]) -> Agent:
        """CLI > the role's file section > env > agent.* > .env > the role's code default > the general code default."""
        role_file, role_default = self.settings.get(ROLES[role]), ROLE_DEFAULTS.get(role, Agent())
        resolved = {}
        for f in fields(Agent):
            n = f.name
            resolved[n] = self._pick(f"{role}.{n}", (
                (cli.get(n), "cli"), (getattr(role_file, n), f"file {self.file} {ROLES[role]}"),
                (getattr(self.environ, n), f"env {AGENT_ENV.get(n)}"),
                (getattr(self.settings.agent, n), f"file {self.file} agent"),
                (getattr(self.dotenv, n), f".env {AGENT_ENV.get(n)}"),
                (getattr(role_default, n), f"default {role}"), (getattr(AGENT_DEFAULT, n), "default")))
        return Agent(**resolved)


def _one_line(e: yaml.YAMLError) -> str:
    mark = getattr(e, "problem_mark", None)
    where = f" at line {mark.line + 1} column {mark.column + 1}" if mark else ""
    return f"{getattr(e, 'problem', None) or 'not YAML'}{where}"


def load(argument: Path | None, environ: Mapping[str, str], dotenv: Mapping[str, str]) -> Loaded:
    path = config_file(argument, environ)
    try:
        settings = parse(read_yaml(path), path.parent) if path else Settings()
    except yaml.YAMLError as e:
        raise ConfigError(f"invalid_yaml: {path}: {_one_line(e)}") from None
    except ConfigError as e:
        raise ConfigError(f"{e} ({path})") from None
    return Loaded(path, settings, _agent_layer(environ, ""), _agent_layer(dotenv, ".env "))
