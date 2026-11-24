from __future__ import annotations

from cryptobench.shared.catalogue.name_layers import ServiceSpellings, merged
from cryptobench.shared.catalogue.names import Names
from ._services import services


def capture_names(base: Names, doc: dict) -> Names:
    """The capture's services as name-layer rows, in capture order."""
    return merged(base, (ServiceSpellings(p["name"], s["type"], s["algorithm"], tuple(str(a) for a in s.get("aliases") or []))
                         for p, s in services(doc)))
