"""catalog/upgrades.yaml: broken canonical name → accepted upgrade targets per family, read and checked whole."""
from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path

from cryptobench import paths
from cryptobench.coded import InputError
from cryptobench.document import AT_PATH, DocumentKind
from cryptobench.catalogue.families import Families
from cryptobench.catalogue.names import Names, fold
from .screening import ACCEPTED, DEPRECATED, Screening
from .types import types

CATALOG = paths.UPGRADES_CATALOG.path
SCHEMA_VERSION = 1


class UpgradesError(InputError):
    pass


UPGRADES_DOC = DocumentKind("upgrades", SCHEMA_VERSION, AT_PATH, UpgradesError)


@dataclass(frozen=True)
class Target:
    name: str
    source: str


@dataclass(frozen=True)
class Upgrades:
    rows: dict[tuple[str, str], tuple[Target, ...]]

    def targets(self, family: str | None, canonical: str | None) -> frozenset[str]:
        """The folded target names of a broken name; empty when it is not listed."""
        if family is None or canonical is None:
            return frozenset()
        return frozenset(fold(t.name) for t in self.rows.get((family, fold(canonical)), ()))

    @classmethod
    def load(cls, path: Path = CATALOG) -> "Upgrades":
        doc = UPGRADES_DOC.read(path)
        names = Names.load()
        return _Reader(names, Screening.load(names=names), Families.load()).upgrades(doc)


class _Reader:

    def __init__(self, names: Names, screening: Screening, families: Families):
        self.names, self.screening, self.families, self.problems = names, screening, families, []

    def upgrades(self, doc: dict) -> Upgrades:
        rows = {}
        for family, listed in doc["families"].items():
            if family not in self.families.by_id:
                self.problems.append(f"upgrades_family: {family} is not in families.yaml")
                continue
            for name, targets in listed.items():
                self._broken(family, name)
                rows[family, fold(name)] = tuple(self._target(family, name, t) for t in targets)
        if self.problems:
            raise UpgradesError("; ".join(self.problems))
        return Upgrades(rows)

    def _canonical(self, family: str, name: str) -> str:
        """The family's engine type, when the name is its own canonical spelling with a type row."""
        engine = self.families.by_id[family].type
        found = self.names.catalogued(engine, name)
        if found.name != name or found.keySize is not None or types().of(family, name) is None:
            self.problems.append(f"upgrades_name: {family} {name} is not a canonical name with a type row")
        return engine

    def _rule(self, engine: str, name: str):
        return self.screening.crypto.get((engine, fold(name)))

    def _broken(self, family: str, name: str) -> None:
        engine = self._canonical(family, name)
        rule = self._rule(engine, name) or self.screening.component(engine, name, self.names)
        if rule is None or rule.status != DEPRECATED:
            self.problems.append(f"upgrades_not_broken: {family} {name} is not screened broken")

    def _target(self, family: str, broken: str, raw: dict) -> Target:
        name, source = raw.get("name"), raw.get("source")
        rule = self._rule(self._canonical(family, name), name)
        if rule is None or rule.status != ACCEPTED:
            self.problems.append(f"upgrades_target: {family} {broken} -> {name} is not screened accepted")
        if source not in self.screening.sources:
            self.problems.append(f"upgrades_source: {family} {broken} -> {name}: {source!r} is not in screening.yaml sources")
        return Target(name, source)


@cache
def upgrades() -> Upgrades:
    return Upgrades.load()
