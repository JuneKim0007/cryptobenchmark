"""What an agent is shown of the catalogues: one entry as one provider build sees it, the groups, and one group's members a page at a time."""
from __future__ import annotations

import copy

from .algorithms import (
    Algorithms,
    AlgorithmsError,
    algorithm_id,
    algorithms,
)
from .families import UNIDENTIFIED, Families
from .groups import GroupCatalog, group_catalog
from .names import fold
from .overrides import apply_override
from .provider_builds import ProviderBuilds, provider_builds

UNKNOWN = "algorithm_unknown"
PROVIDERS = "providers"


def view_for(identifier: str, provider: str | None = None, catalogue: Algorithms | None = None, builds: ProviderBuilds | None = None) -> dict:
    """provider: a build key "<name> @ <build>", or a name one build carries; none is the base entry. Only that build's differences apply; no other build's section is kept."""
    found = [e for e in (catalogue or algorithms()).entries if fold(e.id) == fold(identifier)]
    if len(found) != 1:
        where = f"is in {len(found)} catalogues: {sorted(e.family for e in found)}" if found else "is in no catalogue"
        raise AlgorithmsError(f"{UNKNOWN}: {identifier} {where}")
    raw = found[0].raw
    view = copy.deepcopy({k: v for k, v in raw.items() if k != PROVIDERS})
    if provider is None:
        return view
    for path, value in (raw[PROVIDERS].get((builds or provider_builds()).resolve(provider)) or {}).items():
        apply_override(view, path, copy.deepcopy(value))
    return view


def _members(group_id: str, groups: GroupCatalog, families: Families) -> list[str]:
    if group_id == UNIDENTIFIED:
        return list(groups.unidentified)
    group = next((g for g in groups.families if g.family == group_id), None)
    if group is None:
        raise AlgorithmsError(f"{UNKNOWN}: group {group_id} is not one of {sorted(families.by_id)}")
    return [algorithm_id(families.by_id[group_id].type, name) for name in group.algorithms]


def list_groups(groups: GroupCatalog | None = None, families: Families | None = None) -> list[dict]:
    """Each group's id, description and exemplars, in the file's order, unidentified last."""
    groups, families = groups or group_catalog(), families or Families.load()
    rows = [{"id": g.family, "description": families.by_id[g.family].description, "exemplars": list(g.exemplars)} for g in groups.families]
    return [*rows, {"id": UNIDENTIFIED, "description": families.unidentified.description, "exemplars": []}]


def get_group(group: str, items: int = 10, after: str | None = None, groups: GroupCatalog | None = None,
              families: Families | None = None) -> dict:
    """One page of the group's member ids after `after`, and how many remain behind the page."""
    if type(items) is not int or items < 1:
        raise AlgorithmsError(f"{UNKNOWN}: items {items!r} is not a whole number of at least 1")
    members = _members(group, groups or group_catalog(), families or Families.load())
    folded = [fold(m) for m in members]
    if after is not None and fold(after) not in folded:
        raise AlgorithmsError(f"{UNKNOWN}: {after} is no member of group {group}")
    start = folded.index(fold(after)) + 1 if after is not None else 0
    page = members[start:start + items]
    return {"id": group, "members": page, "remaining": max(0, len(members) - start - len(page))}
