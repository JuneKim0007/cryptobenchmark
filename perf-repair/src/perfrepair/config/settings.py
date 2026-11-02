"""perfrepair.yaml's sections as checked values; parse refuses unknown keys, invalid values and secrets."""
from __future__ import annotations

import re
from dataclasses import MISSING, dataclass, field, fields
from pathlib import Path
from typing import Any, Mapping

BACKENDS = ("claude", "claude-code", "dry-run")
EFFORTS = ("low", "medium", "high", "xhigh", "max")
UNKNOWN = ("model", "unverified")
DEFAULT_MODEL = "claude-opus-5-5"
SECRET_KEY = re.compile(r"api[_-]?key|token|secret|password", re.I)
SECRET_VALUE = re.compile(r"^sk-ant-")


class ConfigError(ValueError):
    pass


class Invalid(ValueError):

    def __init__(self, name: str, value: Any, expected: str):
        super().__init__(name)
        self.name, self.value, self.expected = name, value, expected


def _check(name: str, value: Any, ok: bool, expected: str) -> None:
    if value is not None and not ok:
        raise Invalid(name, value, expected)


def _one_of(name: str, value: Any, choices: tuple[str, ...]) -> None:
    _check(name, value, value in choices, f"one of {list(choices)}")


def _text(name: str, value: Any) -> None:
    _check(name, value, isinstance(value, str) and value != "", "a non-empty string")


def _positive(name: str, value: Any) -> None:
    _check(name, value, isinstance(value, int) and not isinstance(value, bool) and value > 0, "a positive integer")


def _path(name: str, value: Any) -> None:
    _check(name, value, isinstance(value, Path), "a path")


def _path_field():
    return field(default=None, metadata={"path": True})


@dataclass(frozen=True)
class Agent:
    backend: str | None = None
    model: str | None = None
    effort: str | None = None
    claudeBinary: str | None = None

    def __post_init__(self):
        _one_of("backend", self.backend, BACKENDS)
        _text("model", self.model)
        _one_of("effort", self.effort, EFFORTS)
        _text("claudeBinary", self.claudeBinary)


@dataclass(frozen=True)
class Paths:
    run: Path | None = _path_field()
    results: Path | None = _path_field()
    prompts: Path | None = _path_field()

    def __post_init__(self):
        for f in fields(self):
            _path(f.name, getattr(self, f.name))


@dataclass(frozen=True)
class Grouping:
    turns: int | None = None
    sessions: int | None = None
    limit: int | None = None
    assign: Agent = field(default_factory=Agent)
    supervisor: Agent = field(default_factory=Agent)

    def __post_init__(self):
        for name in ("turns", "sessions", "limit"):
            _positive(name, getattr(self, name))


@dataclass(frozen=True)
class Guide:
    mode: str | None = None
    limit: int | None = None
    device: bool | None = None
    config: Path | None = _path_field()
    agent: Agent = field(default_factory=Agent)

    def __post_init__(self):
        # Modes come from result/criteria.yaml, a higher layer; the guide command checks the name.
        _text("mode", self.mode)
        _positive("limit", self.limit)
        _check("device", self.device, isinstance(self.device, bool), "true or false")
        _path("config", self.config)


@dataclass(frozen=True)
class Ai:
    worthiness: Agent = field(default_factory=Agent)
    replace: Agent = field(default_factory=Agent)


@dataclass(frozen=True)
class Screening:
    catalog: Path | None = _path_field()
    unknown: str | None = None

    def __post_init__(self):
        _path("catalog", self.catalog)
        _one_of("unknown", self.unknown, UNKNOWN)


@dataclass(frozen=True)
class Settings:
    agent: Agent = field(default_factory=Agent)
    paths: Paths = field(default_factory=Paths)
    grouping: Grouping = field(default_factory=Grouping)
    guide: Guide = field(default_factory=Guide)
    ai: Ai = field(default_factory=Ai)
    screening: Screening = field(default_factory=Screening)

    def get(self, key: str) -> Any:
        value: Any = self
        for part in key.split("."):
            value = getattr(value, part)
        return value


AGENT_DEFAULT = Agent("claude-code", DEFAULT_MODEL, "medium", "claude")
ROLES = {"grouping.assign": "grouping.assign", "grouping.supervisor": "grouping.supervisor",
         "guide": "guide.agent", "ai.worthiness": "ai.worthiness", "ai.replace": "ai.replace"}
ROLE_DEFAULTS = {"grouping.supervisor": Agent(effort="high")}


def _join(path: str, key: Any) -> str:
    return f"{path}.{key}" if path else str(key)


def _secret(where: str) -> ConfigError:
    return ConfigError(f"secret_key: {where}: keep secrets in the environment or .env")


def _check_keys(cls: type, raw: Any, path: str) -> None:
    if not isinstance(raw, Mapping):
        raise ConfigError(f"invalid: {path or '<root>'} {raw}, a mapping")
    for key in raw:
        if SECRET_KEY.search(str(key)):
            raise _secret(_join(path, key))
    names = [f.name for f in fields(cls)]
    unknown = sorted(str(k) for k in raw if k not in names)
    if unknown:
        raise ConfigError(f"unknown_keys: {path or '<root>'} {unknown}, known {names}")


def _value(f, value: Any, where: str, base: Path) -> Any:
    if isinstance(value, str) and SECRET_VALUE.search(value):
        raise _secret(where)
    if f.default_factory is not MISSING:
        return _section(f.default_factory, value, where, base)
    if f.metadata.get("path") and isinstance(value, str) and value:
        return base / Path(value).expanduser()
    return value


def _section(cls: type, raw: Any, path: str, base: Path):
    _check_keys(cls, raw, path)
    values = {f.name: _value(f, raw[f.name], _join(path, f.name), base)
              for f in fields(cls) if raw.get(f.name) is not None}
    try:
        return cls(**values)
    except Invalid as e:
        raise ConfigError(f"invalid: {_join(path, e.name)} {e.value}, {e.expected}") from None


def parse(document: Any, base: Path) -> Settings:
    """Relative paths resolve against `base`, the config file's folder."""
    return _section(Settings, {} if document is None else document, "", base)
