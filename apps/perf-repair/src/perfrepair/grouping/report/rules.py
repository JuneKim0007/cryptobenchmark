from __future__ import annotations

from typing import Callable

from ...dto.grouping import KEY_APP_HELD, KEY_PROVIDER_HELD, Item, Profile
from ...dto.grouping_output import Finding
from ...dto.grouping_state import Knowledge, code_made
from ...dto.interop import PairResult
from ...catalog.resolved import function_parameters

Rule = Callable[[Knowledge, dict[int, Item], dict[int, Profile]], list[Finding]]


def resolved_parameters_differ(k: Knowledge, items: dict[int, Item], profiles: dict[int, Profile]) -> list[Finding]:
    out = []
    for gid, g in sorted(k.groups.items()):
        fixed = {function_parameters(items[m].resolved) for m in g.members}
        fixed.discard(())
        resolved = {items[m].resolved for m in g.members if function_parameters(items[m].resolved) in fixed}
        if len(fixed) > 1:
            out.append(Finding("resolved_parameters_differ", "error", gid, tuple(g.members),
                               "members resolved different parameters: " + " | ".join(sorted(resolved))))
    return out


def key_contract_differs(k: Knowledge, items: dict[int, Item], profiles: dict[int, Profile]) -> list[Finding]:
    return [Finding("key_contract_differs", "error", gid, tuple(g.members),
                    "members hold application-held keys and keys inside the provider: not interchangeable")
            for gid, g in sorted(k.groups.items())
            if {KEY_APP_HELD, KEY_PROVIDER_HELD} <= {profiles[m].keyContract for m in g.members}]


def key_contract_conflict(k: Knowledge, items: dict[int, Item], profiles: dict[int, Profile]) -> list[Finding]:
    """A generator's trial and its provider's consumers disagree on where the key lives: it is unknown, alone."""
    return [Finding("key_contract_conflict", "warning", k.group_of(m), (m,), f"{items[m].qualified}: {p.keyContractConflict}")
            for m, p in sorted(profiles.items()) if p.keyContractConflict and m in items]


def _assumed(members: list[int], profiles: dict[int, Profile]) -> list[str]:
    return sorted({a for m in members if profiles[m].signature for a in profiles[m].signature.assumed})


def convention_assumed(k: Knowledge, items: dict[int, Item], profiles: dict[int, Profile]) -> list[Finding]:
    """A code-made group of two or more whose join rests on what no member's data confirms; interop measures it."""
    return [Finding("convention_assumed", "warning", gid, tuple(g.members),
                    f"grouped by provider convention, not recorded data: {', '.join(_assumed(g.members, profiles))}")
            for gid, g in sorted(k.groups.items())
            if code_made(gid) and len(g.members) > 1 and _assumed(g.members, profiles)]


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


RULES: tuple[Rule, ...] = (resolved_parameters_differ, key_contract_differs, key_contract_conflict, convention_assumed, no_common_key_size, no_runnable_member, singleton, dropped)


def check(k: Knowledge, items: dict[int, Item], profiles: dict[int, Profile]) -> list[Finding]:
    return [f for rule in RULES for f in rule(k, items, profiles)]


def interop_failed(results: list[PairResult], ids: dict[str, int]) -> list[Finding]:
    return [Finding("interop_failed", "error", r.group, (ids[r.a], ids[r.b]),
                    f"{r.a} and {r.b} do not interoperate, never an option for each other: {r.reason}")
            for r in results if r.result == "fail"]


def interop_not_checkable(results: list[PairResult], ids: dict[str, int]) -> list[Finding]:
    return [Finding("interop_not_checkable", "info", r.group, (ids[r.a], ids[r.b]), f"{r.a} and {r.b}: {r.reason}")
            for r in results if r.result == "not_checkable"]


INTEROP_RULES = (interop_failed, interop_not_checkable)


def check_interop(results: list[PairResult] | None, items: dict[int, Item]) -> list[Finding]:
    ids = {i.qualified: i.id for i in items.values()}
    return [f for rule in INTEROP_RULES for f in rule(results or [], ids)]
