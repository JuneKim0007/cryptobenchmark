"""Where a site meets the device's primitives: explicit provider, or the first by manifest precedence that registers it."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .. import run_dir as rd
from ..catalog.names import Names, NamesError
from ..data_handler.inbound import Probe, RunContext
from ..dto import ProviderEntry
from ..dto.site import NOT_ON_DEVICE

NAME_CONFLICT = "name_conflict"
from .find.scan import Site
from ..stop.halt import Coded


def default_provider(probe: Probe, providers: list[ProviderEntry], engine_type: str,
                     algorithm: str) -> tuple[str, str] | None:
    for p in sorted(providers, key=lambda p: p.precedence):
        name = probe.index.registered(p.name, engine_type, algorithm)
        if name is not None:
            return p.name, name
    return None


def resolve(site: Site, probe: Probe, names: Names, providers: list[ProviderEntry]) -> dict:
    """missing: the provider, or the name no provider registers, that a not_on_device site needs; never dropped."""
    alg = site.algorithm.literal
    try:
        canonical = names.canonical(site.engineType, alg) if alg is not None else None
    except NamesError:
        # providers mean two functions by this spelling: kept and logged, never a stop
        return site.to_json() | {"resolvedProvider": None, "resolvedAlgorithm": alg, "resolution": NAME_CONFLICT,
                                 "missing": None, "canonicalAlgorithm": None, "canonicalKeySize": None}
    on_device, missing = {p.name for p in providers}, None
    if site.provider is not None:
        name = site.provider.literal
        if name is None:
            provider, alg, resolution = None, None, "unresolved_provider"
        elif name not in on_device:
            provider, alg, resolution, missing = name, canonical and canonical.name, NOT_ON_DEVICE, name
        elif alg is None:
            provider, resolution = name, "unresolved_algorithm"
        else:
            provider, alg, resolution = name, probe.index.registered(name, site.engineType, alg) or canonical.name, "explicit"
    elif alg is None:
        provider, resolution = None, "unresolved_algorithm"
    else:
        hit = default_provider(probe, providers, site.engineType, alg)
        provider, alg, resolution = (hit[0], hit[1], "default") if hit else (None, canonical.name, NOT_ON_DEVICE)
        missing = None if hit else f"{site.engineType} {canonical.name}"
    return site.to_json() | {"resolvedProvider": provider, "resolvedAlgorithm": alg, "resolution": resolution,
                             "missing": missing, "canonicalAlgorithm": canonical and canonical.name,
                             "canonicalKeySize": canonical and canonical.keySize}


@dataclass(frozen=True)
class Primitives:
    context: RunContext

    @classmethod
    def load(cls, device: Path) -> "Primitives":
        context = RunContext.load(Path(device) / rd.MANIFEST)
        if context.file("probe") is None:
            raise Coded(f"missing_probe: {context.path}: no probe file; resolving a site needs the device's providers")
        return cls(context)

    @property
    def names(self) -> Names:
        return self.context.names

    def resolve(self, site: Site) -> dict:
        return resolve(site, self.context.probe, self.context.names, self.context.manifest.providers)
