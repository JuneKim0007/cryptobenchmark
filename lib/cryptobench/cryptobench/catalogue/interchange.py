from __future__ import annotations

from .paths import DATA
import re
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

import yaml

from ..coded import InputError
from ..document import AT_PATH, DocumentKind

CATALOG = DATA / "interchange.yaml"
SCHEMA_VERSION = 1
INTERCHANGE_DOC = DocumentKind("interchange", SCHEMA_VERSION, AT_PATH)
KEY_NONE, KEY_ASSUMED, KEY_ASKED = "none", "assumed", "asked"
INPUT, KEY, OUTPUT = "input", "key", "output"


@dataclass(frozen=True)
class Rule:
    match: re.Pattern
    set: dict[str, str]
    convention: dict[str, str]
    unknown: tuple[str, ...]
    resolved: tuple[str, ...]

    @property
    def components(self) -> set[str]:
        return {*self.set, *self.convention, *self.unknown, *self.resolved}


@dataclass(frozen=True)
class Engine:
    splits: tuple[str, ...]
    key: str
    defaults: dict[str, str]
    rules: tuple[Rule, ...]

    def rule_of(self, canonical: str) -> tuple[Rule, dict[str, str]] | None:
        for rule in self.rules:
            found = rule.match.fullmatch(canonical)
            if found:
                return rule, found.groupdict()
        return None


@dataclass(frozen=True)
class Interchange:
    engines: dict[str, Engine]
    digest_components: frozenset[str]
    contracts: dict[str, frozenset[str]] = field(default_factory=dict)

    def contract_of(self, component: str) -> str:
        return next((c for c, names in self.contracts.items() if component in names), OUTPUT)


def _rule(row: dict) -> Rule:
    return Rule(re.compile(row["match"], re.IGNORECASE), row.get("set") or {}, row.get("convention") or {},
                tuple(row.get("unknown") or ()), tuple(row.get("resolved") or ()))


def _engine(engine_type: str, row: dict) -> Engine:
    engine = Engine(tuple(row["splits"]), row["key"], row.get("defaults") or {}, tuple(_rule(r) for r in row["rules"]))
    if engine.key not in (KEY_NONE, KEY_ASSUMED, KEY_ASKED):
        raise InputError(f"interchange_key: {engine_type}: {engine.key!r}")
    stray = sorted({*engine.defaults, *(c for r in engine.rules for c in r.components)} - set(engine.splits))
    if stray:
        raise InputError(f"interchange_component: {engine_type}: {stray} not in its splits")
    return engine


def load(path: Path = CATALOG) -> Interchange:
    doc = yaml.safe_load(Path(path).read_text())
    INTERCHANGE_DOC.check(doc, path)
    return Interchange({t: _engine(t, row) for t, row in doc["engines"].items()}, frozenset(doc["digestComponents"]),
                       {c: frozenset(n) for c, n in doc["contracts"].items()})


@cache
def interchange() -> Interchange:
    return load()
