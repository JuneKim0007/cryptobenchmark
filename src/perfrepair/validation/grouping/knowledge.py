"""Knowledge: well-formed groups, every member a known item of the group's family and in one group only,
no dropped item in a group, and identical to replaying the outbox."""
from __future__ import annotations

from collections import Counter

from ...dto.grouping import Item
from ...dto.grouping_state import Knowledge, OutboxRecord
from ...grouping.catalog.families import Families
from ...grouping.state.knowledge import project
from .answer import SLUG, description_problems


def validate_knowledge(knowledge: Knowledge, records: list[OutboxRecord], items: dict[int, Item],
                       families: Families) -> list[str]:
    problems = []
    for gid, g in knowledge.groups.items():
        if not SLUG.match(gid) or gid in families.by_id:
            problems.append(f"group {gid!r}: not a valid group id")
        if g.family not in families.by_id:
            problems.append(f"group {gid}: family {g.family!r} is not in the catalog")
        problems += description_problems(f"group {gid}", g.description)
        if not g.members:
            problems.append(f"group {gid}: no members")
        for m in g.members:
            if m not in items:
                problems.append(f"group {gid}: member {m} is not an item")
            elif items[m].family != g.family:
                problems.append(f"group {gid}: member {m} is in family {items[m].family}, not {g.family}")
    placed = Counter(m for g in knowledge.groups.values() for m in g.members)
    problems += [f"item {m}: in {n} groups" for m, n in placed.items() if n > 1]
    problems += [f"item {m}: dropped but in a group" for m in knowledge.dropped if m in placed]
    if knowledge.version != len(records):
        problems.append(f"version {knowledge.version} is not the {len(records)} records written")
    try:
        if project(records, items).to_json() != knowledge.to_json():
            problems.append("knowledge differs from the replay of the outbox")
    except (KeyError, ValueError) as e:
        problems.append(f"outbox does not replay: {e}")
    return problems
