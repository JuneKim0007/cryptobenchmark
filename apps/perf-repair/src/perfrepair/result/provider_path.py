"""The provider a site is on for one app: named at the call, or by the default order, which the app's own registration of
a provider it ships at position 1 moves ahead of the device's; the order is static reading, never proof (issue #50)."""
from __future__ import annotations

from dataclasses import dataclass

from ..catalog.bundled_providers import BundledCatalog
from ..dto.dossier import NOT_ON_DEVICE
from cryptobench.catalogue.grouping import qualified
from ..dto.shipped import shipped
from ..dto.site import Scope

DEFAULT = "default"
FIRST = "1"
INSERT = "insertProviderAt"


@dataclass(frozen=True)
class SiteProviders:
    """names: each shipped provider's name in this run (the harness alias it measures under); first: the run name of a
    shipped provider the app inserts at position 1."""
    names: dict[str, str]
    first: str | None = None

    def on(self, s: Scope, items: set[str]) -> tuple[str | None, bool]:
        """The provider the site is on, and whether only the default order says so."""
        named = self.names.get(s.provider or "")
        if s.resolution == NOT_ON_DEVICE and named and s.algorithm and qualified(s.engineType, s.algorithm, named) in items:
            return named, False
        if s.resolution != DEFAULT:
            return s.provider, False
        if self.first and s.algorithm and qualified(s.engineType, s.algorithm, self.first) in items:
            return self.first, True
        return s.provider, True


def site_providers(harness: dict[str, str], app_doc: dict, catalog: BundledCatalog) -> SiteProviders:
    """harness: per provider providers.bundled installed, its group:name; a shipped library it builds is the app's own."""
    by_artifact = {artifact: name for name, artifact in harness.items()}
    names = {s.providerName: by_artifact[s.artifact] for s in shipped(app_doc) if s.providerName and s.artifact in by_artifact}
    rows = [catalog.rows[s.artifact] for s in shipped(app_doc) if s.artifact in by_artifact and s.artifact in catalog.rows]
    first = next((by_artifact[row.artifact] for r in app_doc.get("registers") or [] for row in rows
                  if r.get("call") == INSERT and r.get("position") == FIRST and row.registered_by(r["expr"])), None)
    return SiteProviders(names, first)
