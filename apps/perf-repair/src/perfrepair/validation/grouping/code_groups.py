from __future__ import annotations

from cryptobench.catalogue.groups import group_catalog
from cryptobench.catalogue.grouping import Item, Profile
from ...dto.grouping_state import Group, code_made
from ...dto.screen import Verdict
from ...probe.identified import identified, screened_out
from ...screen.groups import code_groups


def _code_made_problems(gid: str, g: Group, want: Group | None) -> list[str]:
    if want is None:
        return [f"group {gid}: code-made, but screen.json makes no such group"]
    if (g.family, g.description, sorted(g.members)) != (want.family, want.description, want.members):
        return [f"group {gid}: differs from the code-made group screen.json implies "
                f"(members {sorted(g.members)}, expected {want.members})"]
    return []


def _catalog_problems(gid: str, g: Group, want: Group | None) -> list[str]:
    """A model may add a member to a catalog group; what the catalog places in it and how it reads stay."""
    expected = group_catalog().variant_of(gid)
    problems = [f"group {gid}: description differs from the catalog's"] * (g.description != expected.description)
    missing = sorted(set(want.members if want else ()) - set(g.members))
    return problems + [f"group {gid}: misses {missing}, which the catalog places in it"] * bool(missing)


def _member_problems(gid: str, g: Group, want: Group | None, items: dict[int, Item], verdicts: dict[int, Verdict],
                     profiles: dict[int, Profile]) -> list[str]:
    problems = []
    for m in g.members:
        if screened_out(verdicts.get(m)):
            problems.append(f"item {m}: screened {verdicts[m].status}, but in group {gid}; rerun assign")
        elif m in items and identified(items[m], verdicts) and m not in (want.members if want else ()):
            problems.append(f"item {m}: the catalog places it elsewhere, but in group {gid}; rerun assign")
    return problems


def validate_code_groups(groups: dict[str, Group], items: dict[int, Item], verdicts: dict[int, Verdict] | None,
                         profiles: dict[int, Profile]) -> list[str]:
    expected = code_groups(sorted(items.values(), key=lambda i: i.id), verdicts, profiles)
    problems = []
    for gid, g in sorted(groups.items()):
        want = expected.get(gid)
        if code_made(gid):
            problems += _code_made_problems(gid, g, want)
            continue
        if group_catalog().variant_of(gid) is not None:
            problems += _catalog_problems(gid, g, want)
        problems += _member_problems(gid, g, want, items, verdicts or {}, profiles)
    return problems + [f"group {gid}: code-made group missing" for gid in sorted(set(expected) - set(groups))]
