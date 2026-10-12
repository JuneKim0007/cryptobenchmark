"""Static checks over a finished grouping. Each rule proves one thing from recorded data and reports
findings; none changes a group. Add a check by adding a function to RULES."""
from __future__ import annotations

from typing import Callable

from ...dto.grouping import Item, Profile
from ...dto.grouping_output import Finding
from ...dto.grouping_state import Knowledge

Rule = Callable[[Knowledge, dict[int, Item], dict[int, Profile]], list[Finding]]


def resolved_parameters_differ(k: Knowledge, items: dict[int, Item], profiles: dict[int, Profile]) -> list[Finding]:
    out = []
    for gid, g in sorted(k.groups.items()):
        resolved = {items[m].resolved for m in g.members if items[m].resolved}
        if len(resolved) > 1:
            out.append(Finding("resolved_parameters_differ", "error", gid, tuple(g.members),
                               "members resolved different parameters: " + " | ".join(sorted(resolved))))
    return out


def common_key_sizes(members: list[int], profiles: dict[int, Profile]) -> list[int]:
    sized = [set(profiles[m].preparedKeySizes) for m in members if profiles[m].preparedKeySizes]
    return sorted(set.intersection(*sized)) if sized else []


def no_common_key_size(k: Knowledge, items: dict[int, Item], profiles: dict[int, Profile]) -> list[Finding]:
    out = []
    for gid, g in sorted(k.groups.items()):
        sized = [m for m in g.members if profiles[m].preparedKeySizes]
        if len(sized) > 1 and not common_key_sizes(sized, profiles):
            out.append(Finding("no_common_key_size", "warning", gid, tuple(sized),
                               "measured members share no prepared key size"))
    return out


def no_runnable_member(k: Knowledge, items: dict[int, Item], profiles: dict[int, Profile]) -> list[Finding]:
    return [Finding("no_runnable_member", "warning", gid, tuple(g.members), "no member runs on this device")
            for gid, g in sorted(k.groups.items()) if not any(profiles[m].runs for m in g.members)]


def singleton(k: Knowledge, items: dict[int, Item], profiles: dict[int, Profile]) -> list[Finding]:
    return [Finding("singleton", "info", gid, tuple(g.members), "one member: nothing to swap it with")
            for gid, g in sorted(k.groups.items()) if len(g.members) == 1]


def dropped(k: Knowledge, items: dict[int, Item], profiles: dict[int, Profile]) -> list[Finding]:
    return [Finding("dropped", "error", None, (m,), f"{items[m].qualified}: no agent answered acceptably")
            for m in sorted(k.dropped)]


RULES: tuple[Rule, ...] = (resolved_parameters_differ, no_common_key_size, no_runnable_member, singleton, dropped)


def check(k: Knowledge, items: dict[int, Item], profiles: dict[int, Profile]) -> list[Finding]:
    return [f for rule in RULES for f in rule(k, items, profiles)]
