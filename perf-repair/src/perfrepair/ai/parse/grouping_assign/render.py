from __future__ import annotations

from ....dto.grouping import Family, Item
from ....dto.grouping_state import Knowledge

EXAMPLES = 3


def render(item: Item, family: Family, knowledge: Knowledge, items: dict[int, Item]) -> str:
    lines = [f"FAMILY {family.id} — {family.description}", "", "GROUPS IN THIS FAMILY"]
    groups = knowledge.in_family(family.id)
    for gid, g in sorted(groups.items()):
        shown = "; ".join(f"{items[m].name} @ {items[m].provider}" for m in g.members[:EXAMPLES])
        more = f" (+{len(g.members) - EXAMPLES} more)" if len(g.members) > EXAMPLES else ""
        lines += [f"  {gid} ({len(g.members)} members) — {g.description}", f"      e.g. {shown}{more}"]
    if not groups:
        lines.append("  (none yet — create one)")
    lines += ["", "ITEM", f"  id {item.id} · {item.type} · {item.name} · {item.provider}"]
    if item.resolved:
        lines.append(f"  resolved: {item.resolved}")
    return "\n".join(lines)

