"""catalog/groups.yaml: predefined groups by family and canonical name, read and checked whole; it only reduces model calls."""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import yaml

from ..dto.coded import InputError
from ..dto.document import AT_PATH, DocumentKind
from .families import Families
from ..dto.signature import CONVENTION, UNKNOWN, Signature
from .interchange import INPUT, KEY, KEY_NONE, OUTPUT, interchange
from .names import Names, fold

CATALOG = Path(__file__).with_name("groups.yaml")
SCHEMA_VERSION = 1
# two characters short of the answer's id pattern, so the provider-held suffix still matches it
GROUP_ID = re.compile(r"^[a-z0-9][a-z0-9.-]{1,37}$")
PROVIDER_HELD_SUFFIX = ".p"
APP_HELD_TEXT, PROVIDER_HELD_TEXT = "Keys the application holds.", "Keys inside the provider."
ROW_FIELDS = {"id", "description", "contracts", "members"}


class GroupsError(InputError):
    pass


GROUPS_DOC = DocumentKind("groups", SCHEMA_VERSION, "groups_schema: " + AT_PATH, GroupsError)


@dataclass(frozen=True)
class CatalogGroup:
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

    def __init__(self, source: str, groups: tuple[CatalogGroup, ...]):
        self.source, self.groups = source, groups
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


def _member_problems(where: str, engine_type: str, raw: dict, names: Names) -> list[str]:
    if raw["type"] != engine_type:
        return [f"{where}: member {raw['name']} is {raw['type']}, its family holds {engine_type}"]
    found = names.catalogued(raw["type"], raw["name"])
    return [] if found.known and found.name == raw["name"] else [f"{where}: {raw['name']} is no canonical {raw['type']} name"]


def _row_problems(family: str, raw: dict, engine_type: str, seen: set, ids: set, names: Names) -> list[str]:
    where = f"{family} {raw.get('id')}"
    missing, stray = ROW_FIELDS - set(raw), set(raw) - ROW_FIELDS
    if missing or stray:
        return [f"{where}: missing {sorted(missing)}, unknown {sorted(stray)}"]
    found = [f"{where}: id does not match {GROUP_ID.pattern}"] * (not GROUP_ID.match(raw["id"]))
    found += [f"{where}: id listed twice"] * (raw["id"] in ids)
    ids.add(raw["id"])
    for member in raw["members"]:
        found += _member_problems(where, engine_type, member, names)
        found += [f"{where}: {member['name']} listed twice in the family"] * ((family, fold(member["name"])) in seen)
        seen.add((family, fold(member["name"])))
    return found


def load(path: Path = CATALOG, families: Families | None = None, names: Names | None = None) -> GroupCatalog:
    doc = yaml.safe_load(Path(path).read_text())
    GROUPS_DOC.check(doc, path)
    families, names = families or Families.load(), names or Names.load()
    problems, seen, ids, groups = [], set(), set(), []
    for family, rows in doc["families"].items():
        if family not in families.by_id:
            problems.append(f"{family}: not a family of families.yaml")
            continue
        engine_type = families.by_id[family].type
        for raw in rows:
            found = _row_problems(family, raw, engine_type, seen, ids, names)
            problems += found
            if not found:
                groups.append(CatalogGroup(raw["id"], family, raw["description"], raw["contracts"],
                                           tuple((m["type"], m["name"]) for m in raw["members"]),
                                           interchange().engines[engine_type].key == KEY_NONE))
    if problems:
        raise GroupsError("groups_invalid: " + "; ".join(problems))
    return GroupCatalog(doc["source"], tuple(groups))


@cache
def group_catalog() -> GroupCatalog:
    return load(CATALOG)
