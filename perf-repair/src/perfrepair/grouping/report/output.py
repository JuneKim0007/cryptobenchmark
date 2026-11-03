from __future__ import annotations

from ...dto.grouping import Item, Profile
from ...dto.grouping_output import GROUPS_SCHEMA_VERSION, Finding
from ...dto.decision import OutboxRecord
from ...dto.grouping_state import Knowledge
from ...dto.interop import PairResult, interop_section
from ...dto.screen import Verdict
from ...catalog.families import Families
from .rules import common_key_sizes


def _dropped(k: Knowledge, items: dict[int, Item], records: list[OutboxRecord]) -> list[dict]:
    """Under today's ids; a dropped item that left or is screened out now is in no list."""
    ids = {item.key: n for n, item in items.items()}
    return [{"item": ids[r.item], "problems": list(r.problems)} for r in records
            if r.outcome == "dropped" and ids.get(r.item) in k.dropped]


def assemble(k: Knowledge, items: dict[int, Item], profiles: dict[int, Profile], findings: list[Finding],
             records: list[OutboxRecord], families: Families, interop: list[PairResult] | None,
             screen: dict[int, Verdict] | None, not_used: list[int] | None = None) -> dict:
    by_group: dict[str, list[str]] = {}
    for f in findings:
        if f.group:
            by_group.setdefault(f.group, []).append(f.kind)
    used = sorted({g.family for g in k.groups.values()} | {items[m].family for m in k.dropped})
    return {
        "schemaVersion": GROUPS_SCHEMA_VERSION,
        "families": {fid: families.by_id[fid].description for fid in used},
        "groups": [{"id": gid, "family": g.family, "description": g.description, "members": sorted(g.members),
                    "runnable": sorted(m for m in g.members if profiles[m].runs),
                    "keySizes": common_key_sizes(g.members, profiles), "findings": sorted(set(by_group.get(gid, [])))}
                   for gid, g in sorted(k.groups.items())],
        "items": {str(i): {"qualified": items[i].qualified, "group": k.group_of(i), "runs": profiles[i].runs,
                           "measured": profiles[i].measured, "resolved": items[i].resolved,
                           "keyContract": profiles[i].keyContract,
                           "screen": screen[i].status if screen else None} for i in sorted(items)},
        "dropped": _dropped(k, items, records),
        **({} if not_used is None else {"notUsed": sorted(not_used)}),
        "interop": interop_section(interop),
    }
