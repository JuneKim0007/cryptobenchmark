"""A site's provider and algorithm: explicit, or the first provider by manifest precedence that registers it; its canonical name."""
from __future__ import annotations

from ..catalog.names import Names
from ..data_handler.inbound.probe import Probe
from ..dto import ProviderEntry
from .scan import Site


def default_provider(probe: Probe, providers: list[ProviderEntry], engine_type: str,
                     algorithm: str) -> tuple[str, str] | None:
    for p in sorted(providers, key=lambda p: p.precedence):
        name = probe.index.registered(p.name, engine_type, algorithm)
        if name is not None:
            return p.name, name
    return None


def resolve(site: Site, probe: Probe, names: Names, providers: list[ProviderEntry]) -> dict:
    alg = site.algorithm.literal
    canonical = names.canonical(site.engineType, alg) if alg is not None else None
    on_device = {p.name for p in providers}
    if site.provider is not None:
        name = site.provider.literal
        if name is None:
            provider, alg, resolution = None, None, "unresolved_provider"
        elif name not in on_device:
            provider, alg, resolution = name, canonical and canonical.name, "provider_not_on_device"
        elif alg is None:
            provider, resolution = name, "unresolved_algorithm"
        else:
            provider, alg, resolution = name, probe.index.registered(name, site.engineType, alg) or canonical.name, "explicit"
    elif alg is None:
        provider, resolution = None, "unresolved_algorithm"
    else:
        hit = default_provider(probe, providers, site.engineType, alg)
        provider, alg, resolution = (hit[0], hit[1], "default") if hit else (None, canonical.name, "not_registered")
    return site.to_json() | {"resolvedProvider": provider, "resolvedAlgorithm": alg, "resolution": resolution,
                             "canonicalAlgorithm": canonical and canonical.name,
                             "canonicalKeySize": canonical and canonical.keySize}
