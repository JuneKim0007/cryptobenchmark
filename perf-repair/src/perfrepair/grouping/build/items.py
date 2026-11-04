from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from typing import Callable

from ...catalog.names import Names
from ...data_handler.inbound.probe import Probe
from ...dto.grouping import FROM_TRIAL, Item, Profile
from ...catalog.families import Families
from ..signature import signature
from ...catalog.names import fold
from .key_contract import cross_checked, generator_contract, is_generator, key_contract
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


def _primitives(trial: dict):
    """(service, name, entry): what the inventory and so the benchmark hold, each service and each declared transformation
    that ran; a provider declaring modes and paddings has its transformations under no service name of their own."""
    for s in trial["services"]:
        yield s, s["algorithm"], s
        for t in s.get("transformations") or []:
            if t.get("defaultRun"):
                yield s, t["name"], t


def build(probe: Probe, names: Names, trial: dict, families: Families, inventory: dict | None = None,
          prepared: dict | None = None, benchmark: dict | None = None) -> tuple[list[Item], dict[int, Profile]]:
    """Probe and trial suffice; without prepared or benchmark the fields they give are null, never false."""
    runs = _runs(inventory or {})
    context = Context(families, names, probe.generator_kind(names))
    (kinds, sizes), measured = _prepared(prepared), _measured(benchmark)

    drafts, runs_of = {}, {}
    for s, name, entry in _primitives(trial):
        key = (s["provider"], s["type"], name)
        if s["type"] not in families.types or key in drafts:
            continue
        run = entry.get("defaultRun") or {}
        attrs = probe.attributes(s["provider"], s["type"], s["algorithm"])
        formats, classes = _as_list(attrs.get("SupportedKeyFormats")), _as_list(attrs.get("SupportedKeyClasses"))
        kind, source = key_kind(Evidence(s["type"], kinds.get(key), run.get("keyAlgorithm"), formats, classes), context)
        family = families.of(s["type"], kind) or families.of(s["type"], "unknown")
        if family is None:
            raise ValueError(f"{key}: no family for ({s['type']}, {kind}) in the catalog")
        inventoried = runs.get(key, {})
        contract = key_contract(formats, classes)
        drafts[key] = (family.id, run.get("providerChose"), Profile(
            keyKind=kind, keyKindFrom=source, instantiates=bool(entry.get("instantiates")),
            runs=bool(inventoried.get("runs", run.get("works", False))),
            reason=inventoried.get("reason") or run.get("error"),
            defaultKeySize=run.get("keySize"), keyAlgorithm=run.get("keyAlgorithm"), keyProvider=run.get("keyProvider"),
            bareName=bool(run.get("bareName")), measured=measured(key),
            preparedKeySizes=None if sizes is None else tuple(sorted(sizes[key])), keyContract=contract))
        runs_of[key] = [run] if run else []
    for key, (family, resolved, p) in drafts.items():
        provider, engine, name = key
        if is_generator(engine):
            consumers = {d[2].keyContract for k, d in drafts.items() if k[0] == provider and not is_generator(k[1])
                         and fold(d[2].keyAlgorithm or "") == fold(name)}
            contract, conflict = cross_checked(generator_contract(engine, runs_of[key]), consumers)
            p = replace(p, keyContract=contract, keyContractFrom=FROM_TRIAL, keyContractConflict=conflict)
        drafts[key] = (family, resolved, replace(p, signature=signature(engine, name, resolved, p.keyContract, names,
                                                                        key_material=(runs_of[key] or [{}])[0].get("keyMaterial"))))

    order = sorted(drafts, key=lambda k: (drafts[k][0], names.key_or_spelling(k[1], k[2])[0], k[0], k[2]))
    items, profiles = [], {}
    for n, (provider, engine, name) in enumerate(order, 1):
        family, resolved, profile = drafts[(provider, engine, name)]
        items.append(Item(n, engine, name, provider, family, resolved))
        profiles[n] = profile
    return items, profiles
