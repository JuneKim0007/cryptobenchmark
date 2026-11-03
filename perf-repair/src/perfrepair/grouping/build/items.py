from __future__ import annotations

from collections import defaultdict
from typing import Callable

from ...catalog.names import Names, NamesError, fold
from ...data_handler.inbound.probe import Probe
from ...dto.grouping import Item, Profile
from ...catalog.families import Families
from .key_contract import key_contract
from .key_kind import Context, Evidence, key_kind


def _runs(inventory: dict) -> dict[tuple, dict]:
    return {(provider, t, name): entry for provider, types in (inventory.get("providers") or {}).items()
            for t, names in (types or {}).items() for name, entry in (names or {}).items()}


def _as_list(value) -> tuple[str, ...]:
    return tuple(value) if isinstance(value, list) else ((value,) if value else ())


def _prepared(prepared: dict | None) -> tuple[dict, dict | None]:
    """Each case's key kind, and its key sizes; sizes None without prepared.yaml, so an absent size never reads as none."""
    kinds, sizes = {}, defaultdict(set)
    for c in (prepared or {}).get("cases") or []:
        key = (c["provider"], c["type"], c["algorithm"])
        kinds.setdefault(key, (c.get("key") or {}).get("kind"))
        if c.get("keySize"):
            sizes[key].add(c["keySize"])
    return kinds, None if prepared is None else sizes


def _measured(benchmark: dict | None) -> Callable[[tuple], bool | None]:
    if benchmark is None:
        return lambda _: None
    cases = {(c["provider"], c["type"], c["algorithm"]) for c in benchmark.get("cases") or []}
    return lambda key: key in cases


def _sort_name(names: Names, engine_type: str, name: str) -> str:
    """A name_conflict is an item to ask, not a stop; it sorts by its own spelling."""
    try:
        return names.canonical(engine_type, name).key[0]
    except NamesError:
        return fold(name)


def build(probe: Probe, names: Names, trial: dict, families: Families, inventory: dict | None = None,
          prepared: dict | None = None, benchmark: dict | None = None) -> tuple[list[Item], dict[int, Profile]]:
    """Probe and trial suffice; without prepared or benchmark the fields they give are null, never false."""
    runs = _runs(inventory or {})
    context = Context(families, names, probe.generator_kind(names))
    (kinds, sizes), measured = _prepared(prepared), _measured(benchmark)

    drafts = {}
    for s in trial["services"]:
        key = (s["provider"], s["type"], s["algorithm"])
        if s["type"] not in families.types or key in drafts:
            continue
        run = s.get("defaultRun") or {}
        attrs = probe.attributes(*key)
        formats, classes = _as_list(attrs.get("SupportedKeyFormats")), _as_list(attrs.get("SupportedKeyClasses"))
        kind, source = key_kind(Evidence(s["type"], kinds.get(key), run.get("keyAlgorithm"), formats, classes), context)
        family = families.of(s["type"], kind) or families.of(s["type"], "unknown")
        if family is None:
            raise ValueError(f"{key}: no family for ({s['type']}, {kind}) in the catalog")
        inventoried = runs.get(key, {})
        drafts[key] = (family.id, run.get("providerChose"), Profile(
            keyKind=kind, keyKindFrom=source, instantiates=bool(s.get("instantiates")),
            runs=bool(inventoried.get("runs", run.get("works", False))),
            reason=inventoried.get("reason") or run.get("error"),
            defaultKeySize=run.get("keySize"), keyAlgorithm=run.get("keyAlgorithm"), keyProvider=run.get("keyProvider"),
            bareName=bool(run.get("bareName")), measured=measured(key),
            preparedKeySizes=None if sizes is None else tuple(sorted(sizes[key])),
            keyContract=key_contract(formats, classes)))

    order = sorted(drafts, key=lambda k: (drafts[k][0], _sort_name(names, k[1], k[2]), k[0], k[2]))
    items, profiles = [], {}
    for n, (provider, engine, name) in enumerate(order, 1):
        family, resolved, profile = drafts[(provider, engine, name)]
        items.append(Item(n, engine, name, provider, family, resolved))
        profiles[n] = profile
    return items, profiles
