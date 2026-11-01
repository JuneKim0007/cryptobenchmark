from __future__ import annotations

from collections import defaultdict
from typing import Callable

from ...catalog.names import Names
from ...catalog.probe_names import with_probe
from ...dto.grouping import Item, Profile
from ..catalog.families import Families
from .key_kind import Context, Evidence, key_kind

GENERATOR_KINDS = {"KeyGenerator": "secret", "KeyPairGenerator": "pair"}


def _attributes(probe: dict) -> dict[tuple, dict]:
    return {(p["name"], s["type"], s["algorithm"]): s.get("attributes") or {}
            for p in probe["providers"] for s in p.get("services") or []}


def _generator_kind(probe: dict, names: Names) -> Callable[[str], str | None]:
    keys = {(s["type"], names.canonical(s["type"], s["algorithm"]).key)
            for p in probe["providers"] for s in p.get("services") or [] if s["type"] in GENERATOR_KINDS}
    return lambda name: next((kind for engine, kind in GENERATOR_KINDS.items()
                              if (engine, names.canonical(engine, name).key) in keys), None)


def _runs(inventory: dict) -> dict[tuple, dict]:
    return {(provider, t, name): entry for provider, types in (inventory.get("providers") or {}).items()
            for t, names in (types or {}).items() for name, entry in (names or {}).items()}


def _as_list(value) -> tuple[str, ...]:
    return tuple(value) if isinstance(value, list) else ((value,) if value else ())


def build(probe: dict, trial: dict, inventory: dict, prepared: dict, benchmark: dict,
          families: Families) -> tuple[list[Item], dict[int, Profile]]:
    attributes, runs, names = _attributes(probe), _runs(inventory), with_probe(Names.load(), probe)
    context = Context(families, names, _generator_kind(probe, names))
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
        attrs = attributes.get(key, {})
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
