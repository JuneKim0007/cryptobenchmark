from __future__ import annotations

from ....dto.grouping import KEY_LABELS, Family, Item, Profile
from ....dto.grouping_state import Knowledge

EXAMPLES = 3


def _group_key(members: list[int], profiles: dict[int, Profile]) -> list[str]:
    labels = sorted({KEY_LABELS[c] for c in (profiles[m].keyContract for m in members) if c in KEY_LABELS})
    return [f"      key: {', '.join(labels)}"] if labels else []


def render(item: Item, family: Family, knowledge: Knowledge, items: dict[int, Item], profiles: dict[int, Profile]) -> str:
    lines = [f"FAMILY {family.id} — {family.description}", "", "GROUPS IN THIS FAMILY"]
    groups = knowledge.open_groups(family.id)
    for gid, g in sorted(groups.items()):
        shown = "; ".join(f"{items[m].name} @ {items[m].provider}" for m in g.members[:EXAMPLES])
        more = f" (+{len(g.members) - EXAMPLES} more)" if len(g.members) > EXAMPLES else ""
        lines += [f"  {gid} ({len(g.members)} members) — {g.description}", f"      e.g. {shown}{more}"]
        lines += _group_key(g.members, profiles)
    if not groups:
        lines.append("  (none yet — create one)")
    lines += ["", "ITEM", f"  id {item.id} · {item.type} · {item.name} · {item.provider}"]
    if item.resolved:
        lines.append(f"  resolved: {item.resolved}")
    if profiles[item.id].keyContract in KEY_LABELS:
        lines.append(f"  key: {KEY_LABELS[profiles[item.id].keyContract]}")
    return "\n".join(lines)

