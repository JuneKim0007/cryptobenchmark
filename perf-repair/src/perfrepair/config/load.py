"""Finds perfrepair.yaml and resolves each value: CLI > environment > file > .env > code default, recording its source."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from ..files import read_yaml
from .dotenv import ROOT
from .settings import ROLE_DEFAULTS, ROLES, ConfigError, Role, Settings, parse

LOG = logging.getLogger(__name__)
DEFAULT_FILE = ROOT / "perfrepair.yaml"
CONFIG_ENV = "PERFREPAIR_CONFIG"
GATEWAY_ENV = {"gateway": "PERFREPAIR_AGENT", "auth": "PERFREPAIR_AUTH", "model": "PERFREPAIR_MODEL", "effort": "PERFREPAIR_EFFORT"}


def config_file(argument: Path | None, environ: Mapping[str, str]) -> Path | None:
    for path, origin in ((argument, "--perfrepair-config"), (environ.get(CONFIG_ENV), CONFIG_ENV)):
        if path:
            if not Path(path).expanduser().is_file():
                raise ConfigError(f"missing_file: {path} ({origin})")
            return Path(path).expanduser().resolve()
    return DEFAULT_FILE if DEFAULT_FILE.is_file() else None


def _gateway_layer(values: Mapping[str, str]) -> dict[str, str | None]:
    return {name: values.get(var) or None for name, var in GATEWAY_ENV.items()}


@dataclass
class Loaded:
    file: Path | None
    settings: Settings
    environ: Mapping[str, str | None]
    dotenv: Mapping[str, str | None]
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

    def _gateway_key(self, role: str, key: str, cli: Any, block: Any, section: str, default: Any) -> Any:
        """CLI > the role's file section > env > the gateway block > .env > the role's code default > the general code default."""
        role_file, role_default = self.settings.get(ROLES[role]), ROLE_DEFAULTS.get(role, Role())
        return self._pick(f"{role}.{key}", (
            (cli, "cli"), (getattr(role_file, key, None), f"file {self.file} {ROLES[role]}"),
            (self.environ.get(key), f"env {GATEWAY_ENV.get(key)}"), (block, f"file {self.file} {section}"),
            (self.dotenv.get(key), f".env {GATEWAY_ENV.get(key)}"),
            (getattr(role_default, key, None), f"default {role}"), (default, "default")))

    def gateway_name(self, role: str, cli: str | None, default: str) -> str:
        return self._gateway_key(role, "gateway", cli, self.settings.aiGateway.use, "aiGateway.use", default)

    def gateway_values(self, role: str, name: str, defaults: Mapping[str, Any], cli: Mapping[str, Any]) -> dict[str, Any]:
        """defaults: the gateway's keys and code defaults; config does not know a gateway's keys otherwise."""
        block = self.settings.aiGateway.blocks.get(name, {})
        return {key: self._gateway_key(role, key, cli.get(key), block.get(key), f"aiGateway.{name}", default)
                for key, default in defaults.items()}


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
    return Loaded(path, settings, _gateway_layer(environ), _gateway_layer(dotenv))
