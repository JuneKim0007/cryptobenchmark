"""Inverse links a reply leaves on two items: refused on another output or a failed interop, else unverified_interop declared."""
from __future__ import annotations

from ...dto.change import SAME
from ...dto.unit import INVERSE, Link, UnitDossiers


def inverse_problems(unit: UnitDossiers, rows: list[dict]) -> list[str]:
    """Each inverse link whose sides end on two items after the swap: refused when their interop failed, else every
    swapped side declares unverified_interop unless it passed."""
    replaced = {r["scope"]: r for r in rows}
    ends = {d.key: d.current for d in unit.dossiers} | {s.scope: s.current for s in unit.stays}
    ends |= {k: r["option"] for k, r in replaced.items()}
    return [p for k in unit.unit.links if k.kind == INVERSE for p in _link(k, unit, ends, replaced)]


def _output_differs(unit: UnitDossiers, member: str, item: str | None) -> bool:
    d = next(d for d in unit.dossiers if d.key == member)
    return any(o.item == item and o.diff is not None and o.diff.output != SAME for o in d.options)


def _link(k: Link, unit: UnitDossiers, ends: dict[str, str | None], replaced: dict[str, dict]) -> list[str]:
    swapped = [m for m in (k.a, k.b) if m in replaced]
    if not swapped or ends[k.a] == ends[k.b]:
        return []
    alias, status = unit.aliases(), unit.interop(ends[k.a], ends[k.b])
    # another output format on one side only: the other side can no longer read it, whatever interop says
    if any(_output_differs(unit, m, ends[m]) for m in swapped):
        return [f"{alias[k.a]} and {alias[k.b]} are inverse; another output must end both on one item"]
    return _interop_of_ends(k, unit, ends, replaced, swapped, status)


def _interop_of_ends(k: Link, unit: UnitDossiers, ends: dict[str, str | None], replaced: dict[str, dict],
                     swapped: list[str], status: str) -> list[str]:
    alias = unit.aliases()
    if status == "fail":
        return [f"{alias[k.a]} and {alias[k.b]} are inverse, and {ends[k.a]} and {ends[k.b]} failed their interop check"]
    if status == "pass":
        return []
    other = {k.a: k.b, k.b: k.a}
    return [f"{alias[m]}: risks must include unverified_interop: its inverse {alias[other[m]]} ends on "
            f"{ends[other[m]] or 'an unresolved item'}, and their interop is {status}"
            for m in swapped if "unverified_interop" not in replaced[m]["risks"]]
