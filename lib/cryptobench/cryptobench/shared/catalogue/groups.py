"""algorithms/groups.yaml: one predefined group per family, its members the family catalogue's entries, its exemplars read and
checked whole; contract rows come from each member's catalogue contract."""
from __future__ import annotations

from .. import paths
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from ..errors.input_error import InputError
from ..document.document import DocumentKind
from ..log.warn import warn
from .signature import CONVENTION, UNKNOWN, Signature
from .algorithms import (
    CONTRACT_KEY,
    CONTRACT_SIDES,
    KEY_NONE,
    KEY_PASSWORD,
    Algorithms,
    algorithm_id,
    algorithms,
    contract_assumed,
    contract_value,
    split_id,
)
from .families import UNIDENTIFIED, Families
from .interchange import INPUT, KEY, OUTPUT, interchange
from .names import Names, fold

CATALOG = paths.repo().algorithms / "groups.yaml"
SCHEMA_VERSION = 4
PROVIDER_HELD_SUFFIX = ".p"
APP_HELD_TEXT, PROVIDER_HELD_TEXT = "Keys the application holds.", "Keys inside the provider."
PASSWORD_TEXT = "A key derived from a password the application holds."
FAMILY_FIELDS = {"exemplars"}
UNIDENTIFIED_FIELDS = {"algorithms", "exemplars"}
ID_LENGTH = 38


class GroupsError(InputError):
    pass


GROUPS_DOC = DocumentKind("groups", SCHEMA_VERSION, GroupsError)


@dataclass(frozen=True)
class FamilyGroup:
    """algorithms: the members' canonical names, in their catalogue's order; exemplars: ids chosen to show its range."""
    family: str
    algorithms: tuple[str, ...]
    exemplars: tuple[str, ...] = ()


@dataclass(frozen=True)
class CatalogGroup:
    """One contract row of a family: the names whose input and output contracts are equal, so a swap changes nothing."""
    id: str
    family: str
    description: str
    contracts: dict
    members: tuple[tuple[str, str], ...]
    keyless: bool
    password: bool = False


@dataclass(frozen=True)
class GroupVariant:
    """One catalog group at one key contract: a group never mixes key contracts."""
    id: str
    family: str
    description: str


def variant(group: CatalogGroup, provider_held: bool) -> GroupVariant:
    if group.keyless:
        return GroupVariant(group.id, group.family, group.description)
    if group.password:
        return GroupVariant(group.id, group.family, f"{group.description} {PASSWORD_TEXT}")
    gid = group.id + (PROVIDER_HELD_SUFFIX if provider_held else "")
    return GroupVariant(gid, group.family, f"{group.description} {PROVIDER_HELD_TEXT if provider_held else APP_HELD_TEXT}")


class GroupCatalog:

    def __init__(self, source: str, groups: tuple[CatalogGroup, ...], families: tuple[FamilyGroup, ...] = (),
                 engine_types: dict[str, str] | None = None, unidentified: tuple[str, ...] = ()):
        self.source, self.groups, self.families, self.unidentified = source, groups, families, unidentified
        engine = engine_types or {}
        self._family_of = {(fold(engine.get(f.family, "")), fold(n)): f.family for f in families for n in f.algorithms}
        self._family_of.update({tuple(map(fold, split_id(i))): UNIDENTIFIED for i in unidentified if split_id(i)})
        self._listed = {(g.family, fold(name)): g for g in groups for _, name in g.members}
        self._variants = {v.id: v for g in groups for v in (variant(g, False), variant(g, True))}

    def of(self, family: str, canonical: str | None) -> CatalogGroup | None:
        return self._listed.get((family, fold(canonical))) if canonical else None

    def family_of(self, engine_type: str, canonical: str | None) -> str | None:
        """The family that lists the name, whatever a device's evidence says; a listed name needs no key evidence."""
        return self._family_of.get((fold(engine_type), fold(canonical))) if canonical else None

    def variant_of(self, group_id: str) -> GroupVariant | None:
        return self._variants.get(group_id)

    def variants(self) -> list[GroupVariant]:
        return list(self._variants.values())


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


def _shown(value) -> str:
    if contract_assumed(value):
        return f"{contract_value(value)} (assumed)"
    return str(value).lower() if isinstance(value, bool) else str(value)


def _describe(engine_type: str, stands: dict) -> str:
    facts = "; ".join(f"{c}: " + ", ".join(f"{k}={_shown(v)}" for k, v in sorted(stands[c].items())) for c in (INPUT, OUTPUT)
                      if stands[c])
    return f"Predefined {engine_type} group. {facts}."


def _sides(contract: dict) -> dict:
    return {side: {k: contract_value(v) for k, v in contract[side].items()} for side in CONTRACT_SIDES}


def _same(contract: dict) -> tuple:
    return (contract[CONTRACT_KEY], *((side, tuple(sorted(values.items()))) for side, values in _sides(contract).items()))


def _rows(family: str, engine_type: str, ids: list[str], catalogue: Algorithms) -> list[CatalogGroup]:
    """A member with no contract has no row: the model decides it."""
    alike = defaultdict(list)
    for name in sorted((split_id(i)[1] for i in ids), key=fold):
        contract = catalogue.of(family, algorithm_id(engine_type, name)).contract
        if contract is not None:
            alike[_same(contract)].append((name, contract))
    return [CatalogGroup(_row_id(family, row[0][0]), family, _describe(engine_type, row[0][1]), _sides(row[0][1]),
                         tuple((engine_type, n) for n, _ in row), row[0][1][CONTRACT_KEY] == KEY_NONE,
                         row[0][1][CONTRACT_KEY] == KEY_PASSWORD) for row in alike.values()]


def _group_problems(family: str, raw, members: list[str]) -> list[str]:
    if not isinstance(raw, dict) or set(raw) != FAMILY_FIELDS or not isinstance(raw["exemplars"], list):
        return [f"{family}: fields {sorted(raw) if isinstance(raw, dict) else raw!r} are not {sorted(FAMILY_FIELDS)}, a list"]
    listed = {fold(m) for m in members}
    return [f"{family}: exemplar {e} has no entry in {family}'s catalogue" for e in raw["exemplars"] if fold(str(e)) not in listed]


def _unidentified_problems(held) -> list[str]:
    """Only the two group fields, no exemplars (nothing in it shows a range), and each item an id listed once."""
    if not isinstance(held, dict) or set(held) != UNIDENTIFIED_FIELDS:
        return [f"{UNIDENTIFIED}: fields {sorted(held) if isinstance(held, dict) else held!r} are not {sorted(UNIDENTIFIED_FIELDS)}"]
    if not isinstance(held["algorithms"], list) or held["exemplars"] != []:
        return [f"{UNIDENTIFIED}: algorithms is not a list, or exemplars is not empty"]
    found = [f"{UNIDENTIFIED}: {i!r} is no <type>|<name> id" for i in held["algorithms"] if split_id(i) is None]
    repeated = [i for i, n in Counter(fold(str(i)) for i in held["algorithms"]).items() if n > 1]
    return found + [f"{UNIDENTIFIED}: {i} listed twice" for i in repeated]


def load(path: Path = CATALOG, families: Families | None = None, names: Names | None = None,
         catalogue: Algorithms | None = None) -> GroupCatalog:
    doc = GROUPS_DOC.read(path, "groups_invalid")
    families, names, catalogue = families or Families.load(), names or Names.load(), catalogue or algorithms()
    problems, groups, rows = [], [], []
    if not isinstance(doc.get("groups"), dict):
        raise GroupsError(f"groups_invalid: {path}: groups is not a mapping")
    held = doc["groups"].get(UNIDENTIFIED, {"algorithms": [], "exemplars": []})
    problems += _unidentified_problems(held)
    unidentified = tuple(held.get("algorithms") or ()) if isinstance(held, dict) else ()
    problems += [f"{f}: not a family of families.yaml" for f in doc["groups"] if f != UNIDENTIFIED and f not in families.by_id]
    sections = [f for f in doc["groups"] if f in families.by_id and f != UNIDENTIFIED]
    for family in sections + [f.id for f in families.all if f.id not in doc["groups"]]:
        members = [e.id for e in catalogue.entries if e.family == family]
        raw = doc["groups"].get(family, {"exemplars": []})
        found = _group_problems(family, raw, members)
        problems += found
        if not found and (members or family in doc["groups"]):
            groups.append(FamilyGroup(family, tuple(split_id(i)[1] for i in members), tuple(raw["exemplars"])))
            rows += _rows(family, families.by_id[family].type, members, catalogue)
    both = {fold(algorithm_id(families.by_id[g.family].type, n)) for g in groups for n in g.algorithms} & {fold(i) for i in unidentified}
    problems += [f"{i}: listed in a family and in {UNIDENTIFIED}" for i in sorted(both)]
    held = {fold(i) for i in unidentified} | {fold(e.id) for e in catalogue.entries}
    for unbuilt in (algorithm_id(t, c) for t in sorted({f.type for f in families.all})
                    for c in sorted(set(names.names.get(t, {}).values())) if fold(algorithm_id(t, c)) not in held):
        warn(f"name_unbuilt: {unbuilt}: names-file canonical with no catalogue entry, not in {UNIDENTIFIED}")
    repeated = [gid for gid, n in Counter(r.id for r in rows).items() if n > 1]
    problems += [f"{gid}: row id listed twice" for gid in repeated]
    if problems:
        raise GroupsError("groups_invalid: " + "; ".join(problems))
    return GroupCatalog(doc["source"], tuple(rows), tuple(groups), {f.id: f.type for f in families.all}, unidentified)


@cache
def group_catalog() -> GroupCatalog:
    return load(CATALOG)
