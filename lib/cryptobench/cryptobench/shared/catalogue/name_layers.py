"""The capture's provider aliases over the names file: the base answers every spelling it knows, the capture adds the rest."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

from .names import Canonical, Names, fold


@dataclass(frozen=True)
class ServiceSpellings:
    provider: str
    type: str
    algorithm: str
    aliases: tuple[str, ...]


def merged(base: Names, capture: Iterable[ServiceSpellings] | None = None) -> Names:
    """One left fold in capture order: a base-known alias meant otherwise is a conflict the base wins; a base-unknown one meant
    two ways is a conflict a user-written lookup refuses."""
    added: dict[tuple[str, str], Canonical] = {}
    said: dict[tuple[str, str], set[str]] = {}
    conflicts: dict[tuple[str, str], str] = {}
    for service in capture or ():
        target = base.catalogued(service.type, service.algorithm)
        for alias in service.aliases:
            at = (service.type, fold(alias))
            static = base.catalogued(service.type, alias)
            said.setdefault(at, set()).add(f"{service.provider} says {target.name}")
            if static.known and static.key != target.key:
                conflicts[at] = f"catalog says {static.name}; " + ", ".join(sorted(said[at]))
            elif not static.known and added.setdefault(at, target).key != target.key:
                conflicts[at] = ", ".join(sorted(said[at]))
    return replace(base, probe=added, conflicts=conflicts)
