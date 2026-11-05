"""catalog/groups.yaml: one predefined group per family, read and checked whole; contract rows are derived from its names."""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import yaml

from ..dto.coded import InputError
from ..dto.document import AT_PATH, DocumentKind
from ..dto.grouping import KEY_APP_HELD
from ..dto.signature import CONVENTION, UNKNOWN, Signature
from .families import Families
from .interchange import INPUT, KEY, KEY_NONE, OUTPUT, interchange
from .names import Names, fold
from .signature import signature

CATALOG = Path(__file__).with_name("groups.yaml")
SCHEMA_VERSION = 2
PROVIDER_HELD_SUFFIX = ".p"
APP_HELD_TEXT, PROVIDER_HELD_TEXT = "Keys the application holds.", "Keys inside the provider."
GROUP_FIELDS = {"description", "algorithms"}
ID_LENGTH = 38


class GroupsError(InputError):
    pass


GROUPS_DOC = DocumentKind("groups", SCHEMA_VERSION, "groups_schema: " + AT_PATH, GroupsError)


@dataclass(frozen=True)
class FamilyGroup:
    family: str
    description: str
    algorithms: tuple[str, ...]


@dataclass(frozen=True)
class CatalogGroup:
    """One contract row of a family: the names whose input and output contracts are equal, so a swap changes nothing."""
    id: str
    family: str
    description: str
    contracts: dict
    members: tuple[tuple[str, str], ...]
    keyless: bool


@dataclass(frozen=True)
class GroupVariant:
    """One catalog group at one key contract: a group never mixes key contracts."""
    id: str
    family: str
    description: str


def _variant(group: CatalogGroup, provider_held: bool) -> GroupVariant:
    if group.keyless:
        return GroupVariant(group.id, group.family, group.description)
    gid = group.id + (PROVIDER_HELD_SUFFIX if provider_held else "")
    return GroupVariant(gid, group.family, f"{group.description} {PROVIDER_HELD_TEXT if provider_held else APP_HELD_TEXT}")


class GroupCatalog:

    def __init__(self, source: str, groups: tuple[CatalogGroup, ...], families: tuple[FamilyGroup, ...] = ()):
        self.source, self.groups, self.families = source, groups, families
        self._listed = {(g.family, fold(name)): g for g in groups for _, name in g.members}
        self._variants = {v.id: v for g in groups for v in (_variant(g, False), _variant(g, True))}

    def of(self, family: str, canonical: str | None) -> CatalogGroup | None:
        return self._listed.get((family, fold(canonical))) if canonical else None

    def variant_of(self, group_id: str) -> GroupVariant | None:
        return self._variants.get(group_id)

    def variants(self) -> list[GroupVariant]:
        return list(self._variants.values())


def variant(group: CatalogGroup, provider_held: bool) -> GroupVariant:
    return _variant(group, provider_held)


def row_contracts(signatures: list[Signature]) -> dict:
    """A row's `contracts`: what every signature states alike; the key contract splits at build, so no row states it."""
    table, out = interchange(), {INPUT: {}, OUTPUT: {}}
    shown = [{c.name: f"{c.value} (assumed)" if c.status == CONVENTION else c.value
              for c in s.components if c.status != UNKNOWN and table.contract_of(c.name) != KEY} for s in signatures]
    for name, value in sorted(shown[0].items() if shown else ()):
        if all(s.get(name) == value for s in shown):
            out[table.contract_of(name)][name] = value
    return out


def _row_id(family: str, name: str) -> str:
    """The family's first letters first: one name can sit in two families, so its id cannot be the name alone."""
    slug = re.sub(r"[^a-z0-9.-]+", "-", name.lower()).strip("-")
    engine, kind = family.split(".")
    return f"{engine[:6]}-{kind[0]}-{slug}"[:ID_LENGTH].rstrip("-.")


def _describe(engine_type: str, stands: dict) -> str:
    facts = "; ".join(f"{c}: " + ", ".join(f"{k}={v}" for k, v in sorted(stands[c].items())) for c in (INPUT, OUTPUT) if stands[c])
    return f"Predefined {engine_type} group. {facts}."


def _rows(family: str, engine_type: str, algorithms: list[str], names: Names) -> list[CatalogGroup]:
    """A name its signature leaves open has no row: the model decides it."""
    table, alike = interchange(), defaultdict(list)
    for name in sorted(algorithms, key=fold):
        read = signature(engine_type, name, None, KEY_APP_HELD, names)
        if read.decided:
            alike[tuple(i for i in read.identity if table.contract_of(i[0]) != KEY)].append((name, read))
    keyless = table.engines[engine_type].key == KEY_NONE
    return [CatalogGroup(_row_id(family, row[0][0]), family, _describe(engine_type, stands := row_contracts([row[0][1]])), stands,
                         tuple((engine_type, n) for n, _ in row), keyless) for row in alike.values()]


def _group_problems(family: str, raw: dict, engine_type: str, names: Names) -> list[str]:
    missing, stray = GROUP_FIELDS - set(raw), set(raw) - GROUP_FIELDS
    if missing or stray:
        return [f"{family}: missing {sorted(missing)}, unknown {sorted(stray)}"]
    found, seen = [f"{family}: description is empty"] * (not raw["description"]), set()
    for name in raw["algorithms"]:
        read = names.catalogued(engine_type, name)
        found += [f"{family}: {name} is no canonical {engine_type} name"] * (not (read.known and read.name == name))
        found += [f"{family}: {name} listed twice"] * (fold(name) in seen)
        seen.add(fold(name))
    return found


def load(path: Path = CATALOG, families: Families | None = None, names: Names | None = None) -> GroupCatalog:
    doc = yaml.safe_load(Path(path).read_text())
    GROUPS_DOC.check(doc, path)
    families, names = families or Families.load(), names or Names.load()
    problems, groups, rows = [], [], []
    if not isinstance(doc.get("groups"), dict):
        raise GroupsError(f"groups_invalid: {path}: groups is not a mapping")
    for family, raw in doc["groups"].items():
        if family not in families.by_id:
            problems.append(f"{family}: not a family of families.yaml")
            continue
        engine_type = families.by_id[family].type
        found = _group_problems(family, raw, engine_type, names)
        problems += found
        if not found:
            groups.append(FamilyGroup(family, raw["description"], tuple(raw["algorithms"])))
            rows += _rows(family, engine_type, raw["algorithms"], names)
    repeated = [gid for gid, n in Counter(r.id for r in rows).items() if n > 1]
    problems += [f"{gid}: row id listed twice" for gid in repeated]
    if problems:
        raise GroupsError("groups_invalid: " + "; ".join(problems))
    return GroupCatalog(doc["source"], tuple(rows), tuple(groups))


@cache
def group_catalog() -> GroupCatalog:
    return load(CATALOG)
