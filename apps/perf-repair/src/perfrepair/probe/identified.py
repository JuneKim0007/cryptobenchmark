"""The one test of identified: an item code places without a model, because screening put it out or the catalogue lists it."""
from __future__ import annotations

from cryptobench.catalogue.algorithms import algorithm_id
from cryptobench.catalogue.groups import CatalogGroup, group_catalog
from cryptobench.catalogue.interchange import OUTPUT
from cryptobench.catalogue.names import Names
from ..catalog.resolved import function_parameters
from cryptobench.catalogue.grouping import Item
from ..dto.screen import CODE_GROUPED, Verdict


def screened_out(verdict: Verdict | None) -> bool:
    return verdict is not None and verdict.status in CODE_GROUPED


def _resolved_agrees(item: Item, group: CatalogGroup) -> bool:
    """A name is not its parameters: what the trial resolved must be what the row states, else the model decides."""
    stated = group.contracts.get(OUTPUT) or {}
    return all(stated.get(name) == value for name, value in function_parameters(item.resolved))


def listed(item: Item, verdict: Verdict | None) -> CatalogGroup | None:
    """The item's contract row: its canonical name has one in its family, and the trial agrees with it."""
    group = group_catalog().of(item.family, verdict.canonical) if verdict is not None else None
    return group if group is not None and _resolved_agrees(item, group) else None


def alias_conflicts(names: Names) -> list[tuple[str, str]]:
    """Each device alias the catalog or another provider names otherwise, as (Type|alias, both sides): a catalogued name keeps
    the catalog's function; an uncatalogued one is asked."""
    return sorted((algorithm_id(engine_type, alias), why) for (engine_type, alias), why in names.conflicts.items())


def identified(item: Item, verdicts: dict[int, Verdict] | None) -> bool:
    """Never asked: screened out, or listed; never without screen.json: runs built before screening ask every item."""
    verdict = (verdicts or {}).get(item.id)
    return verdict is not None and (screened_out(verdict) or listed(item, verdict) is not None)
