"""A unit's links in the replacement message, and each inverse pair's interop per choice a replace leaves."""
from __future__ import annotations

from collections import Counter

from ...dto.unit import INVERSE, Link, UnitDossiers


def _ends(u: UnitDossiers, member: str) -> list[tuple[str, str | None]]:
    d = next((d for d in u.dossiers if d.key == member), None)
    if d is None:
        return [("current", next(s.current for s in u.stays if s.scope == member))]
    return [(o.alias, o.item) for o in d.options]


def _choices(u: UnitDossiers, k: Link, alias: dict[str, str]) -> list[tuple[str, str]]:
    if not any(d.key in (k.a, k.b) for d in u.dossiers):
        return []
    return [(f"{alias[k.a]} {x} with {alias[k.b]} {y}", u.interop(i, j))
            for x, i in _ends(u, k.a) for y, j in _ends(u, k.b) if i != j]


def _pairs(u: UnitDossiers, k: Link, alias: dict[str, str]) -> list[str]:
    """The interop of each two items a replace leaves the sides on; the commonest status once, as every other choice."""
    found = _choices(u, k, alias)
    if not found:
        return []
    common = Counter(s for _, s in found).most_common(1)[0][0]
    rest = [f"    {choice}: interop {s}" for choice, s in found if s != common]
    return rest + [f"    {'every other choice' if rest else 'every choice'}: interop {common}"]


def link_lines(u: UnitDossiers) -> list[str]:
    alias, lines = u.aliases(), []
    for k in u.unit.links:
        lines.append(f"  {alias[k.a]} {k.kind} {alias[k.b]} ({k.via}): lines {', '.join(map(str, k.aLines))} | "
                     f"lines {', '.join(map(str, k.bLines))}")
        lines += _pairs(u, k, alias) if k.kind == INVERSE else []
    return ["LINKS"] + (lines or ["  none: this unit has one member"])
