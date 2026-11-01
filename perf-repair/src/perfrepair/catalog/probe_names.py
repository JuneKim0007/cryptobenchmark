from __future__ import annotations

from dataclasses import replace

from .names import Canonical, Names, fold


def with_probe(names: Names, probe: dict) -> Names:
    added: dict[tuple[str, str], Canonical] = {}
    said: dict[tuple[str, str], set[str]] = {}
    conflicts: dict[tuple[str, str], str] = {}
    for p in probe.get("providers") or []:
        for s in p.get("services") or []:
            engine, target = s["type"], names.catalogued(s["type"], s["algorithm"])
            for alias in s.get("aliases") or []:
                at = (engine, fold(str(alias)))
                static = names.catalogued(engine, str(alias))
                said.setdefault(at, set()).add(f"{p['name']} says {target.name}")
                if static.known and static.key != target.key:
                    conflicts[at] = f"catalog says {static.name}; " + ", ".join(sorted(said[at]))
                elif not static.known and added.setdefault(at, target).key != target.key:
                    conflicts[at] = ", ".join(sorted(said[at]))
    return replace(names, probe=added, conflicts=conflicts)
