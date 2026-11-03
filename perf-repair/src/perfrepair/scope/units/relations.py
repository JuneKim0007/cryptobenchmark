"""relations.yaml read and checked once: which operations are inverses, which calls produce a key."""
from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path

from ...dto.site import Scope
from ...files import read_yaml

RELATIONS = Path(__file__).with_name("relations.yaml")
SUPPORTED_SCHEMA = 1


@dataclass(frozen=True)
class Relations:
    inverses: dict[str, str]
    steps: dict[str, dict[str, str]]
    producers: dict[str, frozenset[str]]

    def operations(self, s: Scope) -> set[str]:
        by_call = self.steps.get(s.engineType, {})
        return set(s.lifecycle.operations) | {by_call[t.call] for t in s.lifecycle.steps if t.call in by_call}

    def output_lines(self, s: Scope) -> tuple[int, ...]:
        calls = self.producers.get(s.engineType, frozenset())
        return tuple(sorted({t.line for t in s.lifecycle.steps if t.call in calls}))


@cache
def read_relations() -> Relations:
    raw = read_yaml(RELATIONS)
    if raw.get("schemaVersion") != SUPPORTED_SCHEMA:
        raise ValueError(f"relations_schema: {RELATIONS} schemaVersion {raw.get('schemaVersion')}, supported {SUPPORTED_SCHEMA}")
    return Relations(dict(raw["inverses"]), {k: dict(v) for k, v in raw["steps"].items()},
                     {k: frozenset(v) for k, v in raw["producers"].items()})
