from __future__ import annotations

from ....dto.grouping import KEY_LABELS, Family, Item, Profile
from ....dto.grouping_state import Knowledge
from ....dto.signature import CONVENTION, UNKNOWN, Signature

EXAMPLES = 3
KEY = "key"
NOT_KNOWN = "not known"


def _shown(c) -> str:
    if c.status == UNKNOWN:
        return f"{c.name}={NOT_KNOWN}"
    return f"{c.name}={c.value} (assumed)" if c.status == CONVENTION else f"{c.name}={c.value}"


def _item_signature(signature: Signature | None) -> list[str]:
    """The key has its own line."""
    shown = [_shown(c) for c in (signature.components if signature else ()) if c.name != KEY]
    return [f"  signature: {', '.join(shown)}"] if shown else []


def _group_signature(members: list[int], profiles: dict[int, Profile]) -> list[str]:
    """What every member knows alike: the values a join is checked against."""
    known = [profiles[m].signature.known() for m in members if profiles[m].signature]
    common = dict(set.intersection(*(set(k.items()) for k in known))) if known else {}
    shown = [f"{n}={v}" for n, v in sorted(common.items()) if n != KEY]
    return [f"      signature: {', '.join(shown)}"] if shown else []


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
        lines += _group_signature(g.members, profiles) + _group_key(g.members, profiles)
    if not groups:
        lines.append("  (none yet — create one)")
    lines += ["", "ITEM", f"  id {item.id} · {item.type} · {item.name} · {item.provider}"]
    if item.resolved:
        lines.append(f"  resolved: {item.resolved}")
    lines += _item_signature(profiles[item.id].signature)
    if profiles[item.id].keyContract in KEY_LABELS:
        lines.append(f"  key: {KEY_LABELS[profiles[item.id].keyContract]}")
    return "\n".join(lines)

