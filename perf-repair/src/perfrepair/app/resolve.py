"""A site's provider and canonical algorithm: explicit, or the first provider by manifest precedence that has it."""
from __future__ import annotations

from ..data_handler.inbound.probe_index import ProbeIndex
from ..dto import ProviderEntry
from .scan import Site


def default_provider(index: ProbeIndex, providers: list[ProviderEntry], engine_type: str,
                     algorithm: str) -> tuple[str, str] | None:
    for p in sorted(providers, key=lambda p: p.precedence):
        name = index.canonical(p.name, engine_type, algorithm)
        if name is not None:
            return p.name, name
    return None


def resolve(site: Site, index: ProbeIndex, providers: list[ProviderEntry]) -> dict:
    alg = site.algorithm.literal
    on_device = {p.name for p in providers}
    if site.provider is not None:
        name = site.provider.literal
        if name is None:
            provider, alg, resolution = None, None, "unresolved_provider"
        elif name not in on_device:
            provider, resolution = name, "provider_not_on_device"
        elif alg is None:
            provider, resolution = name, "unresolved_algorithm"
        else:
            provider, alg, resolution = name, index.canonical(name, site.engineType, alg) or alg, "explicit"
    elif alg is None:
        provider, resolution = None, "unresolved_algorithm"
    else:
        hit = default_provider(index, providers, site.engineType, alg)
        provider, alg, resolution = (hit[0], hit[1], "default") if hit else (None, alg, "not_registered")
    return site.to_json() | {"resolvedProvider": provider, "resolvedAlgorithm": alg, "resolution": resolution}
