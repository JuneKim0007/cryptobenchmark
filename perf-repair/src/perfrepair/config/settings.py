"""Reads perfrepair.yaml: refuses a secret anywhere, warns about keys no row knows, holds the raw values for the rows."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Mapping

from ..inputs.resolve import OnInvalid, unknown_key
from ..stop.halt import Coded
from ..inputs.table import known_tree

LOG = logging.getLogger(__name__)
SECRET_KEY = re.compile(r"api[_-]?key|token|secret|password", re.I)
SECRET_VALUE = re.compile(r"^sk-ant-")
USE = "use"


class ConfigError(Coded):
    pass


@dataclass(frozen=True)
class Settings:
    raw: Mapping[str, Any] = field(default_factory=dict)

    def get(self, key: str) -> Any:
        value: Any = self.raw
        for part in key.split("."):
            value = value.get(part) if isinstance(value, Mapping) else None
        return value

    @property
    def blocks(self) -> dict[str, dict[str, Any]]:
        """name -> a gateway's raw keys; config sits below ai/, so the gateway checks its block at spawn."""
        gateways = self.raw.get("aiGateway")
        if not isinstance(gateways, Mapping):
            return {}
        return {str(name): {k: v for k, v in block.items() if v is not None}
                for name, block in gateways.items() if name != USE and isinstance(block, Mapping)}


def _join(path: str, key: Any) -> str:
    return f"{path}.{key}" if path else str(key)


def _secret(where: str) -> ConfigError:
    return ConfigError(f"secret_key: {where}: keep secrets in the environment or .env")


def _refuse_secrets(raw: Any, path: str) -> None:
    if isinstance(raw, str) and SECRET_VALUE.search(raw):
        raise _secret(path)
    if isinstance(raw, Mapping):
        for key, value in raw.items():
            if SECRET_KEY.search(str(key)):
                raise _secret(_join(path, key))
            _refuse_secrets(value, _join(path, key))
    if isinstance(raw, (list, tuple)):
        for i, value in enumerate(raw):
            _refuse_secrets(value, f"{path}[{i}]")


def _holds_error_row(node: Any) -> bool:
    if isinstance(node, Mapping):
        return any(_holds_error_row(child) for child in node.values())
    return node is OnInvalid.ERROR


def _not_a_section(raw: Any, node: Mapping, path: str, origin: str) -> None:
    where = path or "<root>"
    if _holds_error_row(node):
        raise ConfigError(f"invalid: {where} {raw}, a mapping")
    LOG.warning(f"invalid: {where} {raw}, a mapping; ignored ({origin})")


def _read_section(raw: Any, node: Mapping, path: str, origin: str) -> None:
    if not isinstance(raw, Mapping):
        _not_a_section(raw, node, path, origin)
        return
    any_key = next((k for k in node if k.startswith("<")), None)
    for key, value in raw.items():
        where = _join(path, key)
        if key not in node and any_key is None:
            unknown_key(where, node, origin)
            continue
        child = node.get(key, node.get(any_key))
        if isinstance(child, Mapping) and value is not None:
            _read_section(value, child, where, origin)


def parse(document: Any, origin: str) -> Settings:
    """origin: what a warning names as the file."""
    document = {} if document is None else document
    _refuse_secrets(document, "<root>" if isinstance(document, str) else "")
    _read_section(document, known_tree(), "", origin)
    return Settings(document)
