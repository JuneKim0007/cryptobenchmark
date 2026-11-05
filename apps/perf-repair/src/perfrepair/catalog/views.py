"""What an agent is shown of the catalogues: one entry as one provider sees it, and one group's description and ids."""
from __future__ import annotations

import copy

from .algorithms import Algorithms, AlgorithmsError, algorithm_id, algorithms, override_parent
from .families import Families
from .groups import GroupCatalog, group_catalog
from .names import fold

UNKNOWN = "algorithm_unknown"
PROVIDERS = "providers"


def view_for(identifier: str, provider: str, catalogue: Algorithms | None = None) -> dict:
    """The entry's base fields with only this provider's overrides applied; no other provider's section is kept."""
    found = [e for e in (catalogue or algorithms()).entries if fold(e.id) == fold(identifier)]
    if len(found) != 1:
        where = f"is in {len(found)} catalogues: {sorted(e.family for e in found)}" if found else "is in no catalogue"
        raise AlgorithmsError(f"{UNKNOWN}: {identifier} {where}")
    raw = found[0].raw
    view = copy.deepcopy({k: v for k, v in raw.items() if k != PROVIDERS})
    for path, value in (raw[PROVIDERS].get(provider) or {}).items():
        parent, key = override_parent(view, path)
        parent[key] = copy.deepcopy(value)
    return view


def group_view(group_id: str, groups: GroupCatalog | None = None, families: Families | None = None) -> dict:
    """The family's description and its member ids, nothing else."""
    families = families or Families.load()
    group = next((g for g in (groups or group_catalog()).families if g.family == group_id), None)
    if group is None or group_id not in families.by_id:
        raise AlgorithmsError(f"{UNKNOWN}: group {group_id} is in no catalogue")
    engine_type = families.by_id[group_id].type
    return {"description": families.by_id[group_id].description,
            "algorithms": [algorithm_id(engine_type, name) for name in group.algorithms]}
