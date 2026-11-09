"""The used set: the items the target apps' sites resolve to, their groups' members, and for an item not yet grouped every
askable item of its family no known component sets apart; <device>/used.json, validated before writing."""
from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..ai.parse.grouping_assign.kind import GroupingKind
from ..ai.runtime.engine.kind import project
from ..ai.runtime.engine.outbox import active_outbox
from cryptobench.catalogue.names import fold
from ..catalog.upgrades import upgrades
from ..data_handler.inbound import RunContext
from cryptobench.catalogue.grouping import Item, qualified
from ..dto.grouping_state import Knowledge
from ..dto.screen import ACCEPTED, BROKEN
from ..dto.used import CANDIDATE, GROUP, SITE, UPGRADE, VIA, AppUse, UsedItem, UsedSet
from ..files import write_json
from ..log import step
from ..run_dir import AppPaths, GroupingPaths
from ..validation import require
from ..validation.used import validate_used
from .selection import bundled_named


def _site_items(device: Path, app: str, by_name: dict[str, Item]) -> tuple[list[Item], AppUse]:
    sites = rd.read_sites(AppPaths(device, app).sites)["sites"]
    names = [qualified(s["engineType"], s["resolvedAlgorithm"], s["resolvedProvider"]) for s in sites
             if s.get("resolvedProvider") and s.get("resolvedAlgorithm")]
    found = [by_name[n] for n in names if n in by_name]
    return list({i.id: i for i in found}.values()), AppUse(len(sites), len(found))


class _Reach:
    """Who an item brings in: its group's members, or while it has no record, the askable items it could join."""

    def __init__(self, kind: GroupingKind, knowledge: Knowledge, done: set[str]):
        self.kind, self.knowledge, self.done = kind, knowledge, done
        self.askable = {i.id for i in kind.askable()}

    def _members(self, item: int) -> list[int]:
        group = self.knowledge.group_of(item)
        return list(self.knowledge.groups[group].members) if group else []

    def _fits(self, a: Item, b: Item) -> bool:
        sa, sb = self.kind.profiles[a.id].signature, self.kind.profiles[b.id].signature
        return a.family == b.family and (sa is None or sb is None or not sa.differing(sb))

    def _candidates(self, item: Item) -> list[int]:
        if item.id not in self.askable or item.key in self.done:
            return []
        fits = [i for i in self.kind.askable() if self._fits(item, i)]
        return [m for i in fits for m in (i.id, *self._members(i.id))]

    def _upgrades(self, item: Item) -> list[int]:
        """A broken item's accepted family members, narrowed to the upgrade list's when it names any of them."""
        screen = self.kind.screen or {}
        v = screen.get(item.id)
        if v is None or v.status != BROKEN:
            return []
        accepted = [i for i in self.kind.items() if i.family == item.family and i.id in screen
                    and screen[i.id].status == ACCEPTED]
        listed = upgrades().targets(item.family, v.canonical)
        return [i.id for i in [i for i in accepted if fold(screen[i.id].canonical or i.name) in listed] or accepted]

    def of(self, item: Item) -> list[tuple[int, str]]:
        reached = [(m, GROUP) for m in self._members(item.id)] + [(m, CANDIDATE) for m in self._candidates(item)]
        reached += [(m, UPGRADE) for m in self._upgrades(item)]
        return [(m, how) for m, how in reached if m != item.id]


def _harness_providers(device: Path) -> frozenset[str]:
    manifest = Path(device) / rd.MANIFEST
    return frozenset(RunContext.load(manifest).probe.harness_artifacts()) if manifest.is_file() else frozenset()


def used_set(device: Path, apps: list[str], kind: GroupingKind | None = None) -> UsedSet:
    paths = GroupingPaths(device)
    kind = kind or GroupingKind(paths)
    records = active_outbox(paths.root).records()
    reach = _Reach(kind, project(kind, records), {r.item for r in records})
    by_name = {i.qualified: i for i in kind.items()}
    via: dict[int, str] = {}
    needed: dict[int, set[str]] = {}
    uses, found_by_app = {}, {}
    for app in apps:
        found_by_app[app], uses[app] = _site_items(device, app, by_name)
    harness = _harness_providers(device)
    named = bundled_named(kind.items(), kind.screen, harness, [i for found in found_by_app.values() for i in found])
    for app, found in found_by_app.items():
        reached = [(i.id, SITE) for i in found] + [r for i in found for r in reach.of(i)]
        for n, how in reached:
            if kind.by_id[n].provider in harness and kind.by_id[n].qualified not in named:
                continue
            needed.setdefault(n, set()).add(app)
            via[n] = min(via.get(n, how), how, key=VIA.index)
    items = tuple(UsedItem(kind.by_id[n].qualified, via[n], tuple(sorted(needed[n]))) for n in sorted(needed))
    return UsedSet(len(kind.items()), uses, items)


def write_used(device: Path, apps: list[str]) -> UsedSet:
    device = Path(device)
    with step("device", "used") as s:
        kind = GroupingKind(GroupingPaths(device))
        used = used_set(device, apps, kind)
        require(rd.USED, validate_used(used, {i.qualified for i in kind.items()}))
        write_json(device / rd.USED, used.to_json())
        s.count(deviceItems=used.deviceItems, apps=len(used.apps), sites=sum(u.sites for u in used.apps.values()),
                matched=sum(u.matched for u in used.apps.values()), used=len(used.items),
                **{v: used.count(v) for v in VIA})
        s.wrote(device / rd.USED)
    return used


def clear_used(device: Path) -> None:
    """device.filterByApps off: nothing narrows grouping."""
    (Path(device) / rd.USED).unlink(missing_ok=True)
