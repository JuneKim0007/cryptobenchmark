"""Each applied scope's interop partner: the inverse links of units.json, never a name; the producing side is `produce`."""
from __future__ import annotations

from ..dto.unit import INVERSE, Unit


def inverse_partners(units: list[Unit], applied: set[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    links = [k for u in units for k in u.links if k.kind == INVERSE and k.a in applied and k.b in applied]
    for k in sorted(links, key=lambda k: (k.a, k.b)):
        out.setdefault(k.a, {"partner": k.b, "role": "produce"})
        out.setdefault(k.b, {"partner": k.a, "role": "consume"})
    return out
