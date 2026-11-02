from __future__ import annotations

from collections import defaultdict

from ...catalog.names import Names
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


def build(probe: Probe, names: Names, trial: dict, families: Families, inventory: dict | None = None,
          prepared: dict | None = None, benchmark: dict | None = None) -> tuple[list[Item], dict[int, Profile]]:
    """Probe and trial suffice; without prepared or benchmark the fields they give are null, never false."""
    runs = _runs(inventory or {})
    context = Context(families, names, probe.generator_kind(names))
    kinds, sizes = {}, defaultdict(set)
    for c in (prepared or {}).get("cases") or []:
        key = (c["provider"], c["type"], c["algorithm"])
        kinds.setdefault(key, (c.get("key") or {}).get("kind"))
        if c.get("keySize"):
            sizes[key].add(c["keySize"])
    measured = None if benchmark is None else {(c["provider"], c["type"], c["algorithm"]) for c in benchmark.get("cases") or []}

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
            bareName=bool(run.get("bareName")), measured=None if measured is None else key in measured,
            preparedKeySizes=None if prepared is None else tuple(sorted(sizes[key])),
            keyContract=key_contract(formats, classes)))

    order = sorted(drafts, key=lambda k: (drafts[k][0], names.canonical(k[1], k[2]).key[0], k[0], k[2]))
    items, profiles = [], {}
    for n, (provider, engine, name) in enumerate(order, 1):
        family, resolved, profile = drafts[(provider, engine, name)]
        items.append(Item(n, engine, name, provider, family, resolved))
        profiles[n] = profile
    return items, profiles
