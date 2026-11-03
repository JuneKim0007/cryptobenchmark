from __future__ import annotations

from dataclasses import dataclass, field

from ....catalog.names import fold
from ._services import services

SUPPORTED_SCHEMA = 1


@dataclass(frozen=True)
class Service:
    algorithm: str
    modes: frozenset[str] | None = None
    paddings: frozenset[str] | None = None

    def supports(self, mode: str | None, padding: str | None) -> bool:
        return all(want is None or have is None or fold(want) in have
                   for want, have in ((mode, self.modes), (padding, self.paddings)))


@dataclass
class ProbeIndex:
    services: dict[tuple[str, str, str], Service] = field(default_factory=dict)

    @property
    def engine_types(self) -> set[str]:
        return {t for (_, t, _) in self.services}

    def registered(self, provider: str, engine_type: str, algorithm: str) -> str | None:
        direct = self.services.get((provider, engine_type, fold(algorithm)))
        if direct is not None:
            return direct.algorithm
        parts = algorithm.split("/")
        if engine_type != "Cipher" or len(parts) != 3:
            return None
        base, mode, padding = parts
        # JCA's Cipher.getInstance order; a missing Supported* attribute means the service may support it
        for name, need_mode, need_padding in ((f"{base}/{mode}", None, padding), (f"{base}//{padding}", mode, None),
                                              (base, mode, padding)):
            service = self.services.get((provider, engine_type, fold(name)))
            if service is not None and service.supports(need_mode, need_padding):
                return f"{service.algorithm.split('/')[0]}/{mode}/{padding}"
        return None


def _attribute(service: dict, key: str) -> frozenset[str] | None:
    values = (service.get("attributes") or {}).get(key)
    return None if values is None else frozenset(fold(str(v)) for v in values)


def index_of(doc: dict, source: str) -> ProbeIndex:
    if doc.get("schemaVersion") != SUPPORTED_SCHEMA:
        raise ValueError(f"{source}: probe schemaVersion {doc.get('schemaVersion')} is not {SUPPORTED_SCHEMA}")
    by_name: dict[tuple[str, str, str], Service] = {}
    for p, s in services(doc):
        service = Service(s["algorithm"], _attribute(s, "SupportedModes"), _attribute(s, "SupportedPaddings"))
        for n in [s["algorithm"], *(s.get("aliases") or [])]:
            by_name.setdefault((p["name"], s["type"], fold(str(n))), service)
    return ProbeIndex(by_name)
