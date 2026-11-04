from __future__ import annotations

from ...dto.grouping import Item, Profile
from ...dto.grouping_state import Group, code_made
from ...dto.screen import Verdict
from ...screen.groups import code_groups, grouped_by_code, screened_out


def _code_made_problems(gid: str, g: Group, want: Group | None) -> list[str]:
    if want is None:
        return [f"group {gid}: code-made, but screen.json makes no such group"]
    if (g.family, g.description, sorted(g.members)) != (want.family, want.description, want.members):
        return [f"group {gid}: differs from the code-made group screen.json implies "
                f"(members {sorted(g.members)}, expected {want.members})"]
    return []


def _model_made_problems(gid: str, g: Group, verdicts: dict[int, Verdict], profiles: dict[int, Profile]) -> list[str]:
    problems = []
    for m in g.members:
        if screened_out(verdicts.get(m)):
            problems.append(f"item {m}: screened {verdicts[m].status}, but in model group {gid}; rerun assign")
        elif grouped_by_code(m, verdicts, profiles):
            problems.append(f"item {m}: its signature groups it by code, but in model group {gid}; rerun assign")
    return problems


def validate_code_groups(groups: dict[str, Group], items: dict[int, Item], verdicts: dict[int, Verdict] | None,
                         profiles: dict[int, Profile]) -> list[str]:
    expected = code_groups(sorted(items.values(), key=lambda i: i.id), verdicts, profiles)
    problems = []
    for gid, g in sorted(groups.items()):
        problems += (_code_made_problems(gid, g, expected.get(gid)) if code_made(gid)
                     else _model_made_problems(gid, g, verdicts or {}, profiles))
    return problems + [f"group {gid}: code-made group missing" for gid in sorted(set(expected) - set(groups))]
