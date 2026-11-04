from __future__ import annotations

from dataclasses import dataclass, field

from ....catalog.names import fold
from ....dto.document import DocumentKind
from ._services import services

SUPPORTED_SCHEMA = 1
PROBE_DOC = DocumentKind("probe", SUPPORTED_SCHEMA, "{path}: probe schemaVersion {found} is not {version}")


@dataclass(frozen=True)
class Service:
    algorithm: str
    # folded name to the provider's spelling; None: the provider declares none, so it may support any
    modes: dict[str, str] | None = None
    paddings: dict[str, str] | None = None

    def supports(self, mode: str | None, padding: str | None) -> bool:
        return all(want is None or have is None or fold(want) in have
                   for want, have in ((mode, self.modes), (padding, self.paddings)))

    def transformation(self, mode: str, padding: str) -> str:
        """As the trial composes it from what the provider declares, so a site's spelling lands on the same item."""
        return "/".join((self.algorithm.split("/")[0], (self.modes or {}).get(fold(mode), mode),
                         (self.paddings or {}).get(fold(padding), padding)))


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
                return service.transformation(mode, padding)
        return None


def _attribute(service: dict, key: str) -> dict[str, str] | None:
    values = (service.get("attributes") or {}).get(key)
    return None if values is None else {fold(str(v)): str(v) for v in values}


def index_of(doc: dict, source: str) -> ProbeIndex:
    PROBE_DOC.check(doc, source)
    by_name: dict[tuple[str, str, str], Service] = {}
    for p, s in services(doc):
        service = Service(s["algorithm"], _attribute(s, "SupportedModes"), _attribute(s, "SupportedPaddings"))
        for n in [s["algorithm"], *(s.get("aliases") or [])]:
            by_name.setdefault((p["name"], s["type"], fold(str(n))), service)
    return ProbeIndex(by_name)
