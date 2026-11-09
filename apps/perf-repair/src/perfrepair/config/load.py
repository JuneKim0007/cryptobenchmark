"""Finds perfrepair.yaml and resolves each value by its layer (docs/settings.md), recording its source."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from cryptobench.coded import InputError
from ..files import read_yaml
from ..inputs.resolve import CLI, Candidate, choose
from ..inputs.table import ROLE_KEYS, Layer, RoleRow, Row
from .dotenv import ROOT
from .settings import ConfigError, Settings, parse

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
    chosen: dict[tuple[str, Any], Any] = field(default_factory=dict)

    def _pick(self, key: str, row: Row, layers: Mapping[Layer, Candidate], check: Callable[[str, Any], None], cli: Any) -> Any:
        if (key, cli) in self.chosen:
            return self.chosen[key, cli]
        picked = choose(key, [layers[layer] for layer in row.chain], check, row.invalid)
        value, source = (picked.value, picked.source) if picked else (None, "default")
        # shown: what a file or the environment chose; the rest stays in the log
        quiet = source == CLI or source.startswith("default")
        LOG.log(logging.DEBUG if quiet else logging.INFO, "setting %s: %s (%s)", key, value, source)
        self.sources[key] = source
        self.chosen[key, cli] = value
        return value

    def _file_value(self, row: Row) -> Any:
        value = self.settings.get(row.key)
        if row.path and isinstance(value, str) and value:
            return self.file.parent / Path(value).expanduser()
        return value

    def read(self, row: Row, cli: Any = None, check: Callable[[str, Any], None] | None = None) -> Any:
        """check: a row whose choices live in a higher layer gets them from its reader."""
        return self._pick(row.key, row, {
            Layer.CLI: Candidate(cli, CLI), Layer.FILE: Candidate(self._file_value(row), f"file {self.file}"),
            Layer.DEFAULT: Candidate(row.default, "default", explicit=False)}, check or row.check, cli)

    def role_value(self, role: RoleRow, key: str, row: Row, cli: Any, block: tuple[Any, str], default: Any,
                   check: Callable[[str, Any], None]) -> Any:
        """block: the gateway-wide value in the file and where it sits; only a role's own keys read its section."""
        role_file = self.settings.get(f"{role.key}.{key}") if key in ROLE_KEYS else None
        return self._pick(f"{role.key}.{key}", row, {
            Layer.CLI: Candidate(cli, CLI), Layer.ROLE: Candidate(role_file, f"file {self.file} {role.key}"),
            Layer.ENV: Candidate(self.environ.get(key), f"env {GATEWAY_ENV.get(key)}"),
            Layer.BLOCK: Candidate(block[0], f"file {self.file} {block[1]}"),
            Layer.DOTENV: Candidate(self.dotenv.get(key), f".env {GATEWAY_ENV.get(key)}"),
            Layer.ROLE_DEFAULT: Candidate(role.defaults.get(key), f"default {role.key}", explicit=False),
            Layer.DEFAULT: Candidate(default, "default", explicit=False)}, check, cli)


def load(argument: Path | None, environ: Mapping[str, str], dotenv: Mapping[str, str]) -> Loaded:
    path = config_file(argument, environ)
    try:
        settings = parse(read_yaml(path), str(path)) if path else Settings()
    except ConfigError as e:
        raise ConfigError(f"{e} ({path})") from None
    except InputError as e:
        raise ConfigError(str(e), e.path) from None
    return Loaded(path, settings, _gateway_layer(environ), _gateway_layer(dotenv))
