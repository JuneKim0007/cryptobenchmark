from __future__ import annotations

import re
from pathlib import Path

from ...dto.grouping import Family, Item
from ...dto.grouping_state import Knowledge
from ...validation.grouping.answer import MAX_DESCRIPTION, SLUG

SYSTEM = Path(__file__).with_name("assign.system.md")
EXAMPLES = 3


def system_prompt() -> str:
    return SYSTEM.read_text().replace("{id_pattern}", SLUG.pattern).replace("{max_description}", str(MAX_DESCRIPTION))


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


def item_id_of(message: str) -> int | None:
    found = re.search(r"^ITEM\n  id (\d+) ", message, re.M)
    return int(found.group(1)) if found else None
