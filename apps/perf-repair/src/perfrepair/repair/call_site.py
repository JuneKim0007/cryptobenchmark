"""A scope's call site as cryptobenchmark measures it alone: the one operation it performs and its pattern's variant."""
from __future__ import annotations

from ..dto.site import Scope
from ..result.configurations import operations, parse_label


def _estimated(dossier: dict, option: str) -> set[str]:
    chosen = next((o for o in dossier.get("options") or () if o["item"] == option), {})
    return {m["op"] for e in chosen.get("estimates") or () if (m := parse_label(e["configuration"]))}


def call_site(scope: Scope, dossier: dict, option: str) -> dict:
    """The lifecycle's operation, else the only one the chosen option is estimated at; null when not one."""
    found = set(operations(scope)) or _estimated(dossier, option)
    return {"operation": next(iter(found)) if len(found) == 1 else None, "variant": scope.pattern}
