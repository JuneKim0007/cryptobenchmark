from __future__ import annotations

from collections import defaultdict

from ...catalog.names import Names
from ...data_handler.inbound.probe import Probe
from ...dto.grouping import Item, Profile
from ...catalog.families import Families
from .key_kind import Context, Evidence, key_kind


def _runs(inventory: dict) -> dict[tuple, dict]:
    return {(provider, t, name): entry for provider, types in (inventory.get("providers") or {}).items()
            for t, names in (types or {}).items() for name, entry in (names or {}).items()}


def _as_list(value) -> tuple[str, ...]:
    return tuple(value) if isinstance(value, list) else ((value,) if value else ())


def build(probe: Probe, names: Names, trial: dict, inventory: dict, prepared: dict, benchmark: dict,
          families: Families) -> tuple[list[Item], dict[int, Profile]]:
    runs = _runs(inventory)
    context = Context(families, names, probe.generator_kind(names))
    kinds, sizes = {}, defaultdict(set)
    for c in prepared.get("cases") or []:
        key = (c["provider"], c["type"], c["algorithm"])
        kinds.setdefault(key, (c.get("key") or {}).get("kind"))
        if c.get("keySize"):
            sizes[key].add(c["keySize"])
    measured = {(c["provider"], c["type"], c["algorithm"]) for c in benchmark.get("cases") or []}

    drafts = {}
    for s in trial["services"]:
        key = (s["provider"], s["type"], s["algorithm"])
        if s["type"] not in families.types or key in drafts:
            continue
        run = s.get("defaultRun") or {}
        attrs = probe.attributes(*key)
        kind, source = key_kind(Evidence(s["type"], kinds.get(key), run.get("keyAlgorithm"),
                                         _as_list(attrs.get("SupportedKeyFormats")),
                                         _as_list(attrs.get("SupportedKeyClasses"))), context)
        family = families.of(s["type"], kind) or families.of(s["type"], "unknown")
        if family is None:
            raise ValueError(f"{key}: no family for ({s['type']}, {kind}) in the catalog")
        inventoried = runs.get(key, {})
        drafts[key] = (family.id, run.get("providerChose"), Profile(
            keyKind=kind, keyKindFrom=source, instantiates=bool(s.get("instantiates")),
            runs=bool(inventoried.get("runs", run.get("works", False))),
            reason=inventoried.get("reason") or run.get("error"),
            defaultKeySize=run.get("keySize"), keyAlgorithm=run.get("keyAlgorithm"), keyProvider=run.get("keyProvider"),
            bareName=bool(run.get("bareName")), measured=key in measured, preparedKeySizes=tuple(sorted(sizes[key]))))

    order = sorted(drafts, key=lambda k: (drafts[k][0], names.canonical(k[1], k[2]).key[0], k[0], k[2]))
    items, profiles = [], {}
    for n, (provider, engine, name) in enumerate(order, 1):
        family, resolved, profile = drafts[(provider, engine, name)]
        items.append(Item(n, engine, name, provider, family, resolved))
        profiles[n] = profile
    return items, profiles
