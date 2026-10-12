from __future__ import annotations

from ...dto.grouping import Item, Profile
from ...dto.grouping_output import SCHEMA_VERSION, Finding
from ...dto.decision import OutboxRecord
from ...dto.grouping_state import Knowledge
from ..catalog.families import Families
from .rules import common_key_sizes


def assemble(k: Knowledge, items: dict[int, Item], profiles: dict[int, Profile], findings: list[Finding],
             records: list[OutboxRecord], families: Families) -> dict:
    by_group: dict[str, list[str]] = {}
    for f in findings:
        if f.group:
            by_group.setdefault(f.group, []).append(f.kind)
    used = sorted({g.family for g in k.groups.values()} | {items[m].family for m in k.dropped})
    return {
        "schemaVersion": SCHEMA_VERSION,
        "families": {fid: families.by_id[fid].description for fid in used},
        "groups": [{"id": gid, "family": g.family, "description": g.description, "members": sorted(g.members),
                    "runnable": sorted(m for m in g.members if profiles[m].runs),
                    "keySizes": common_key_sizes(g.members, profiles), "findings": sorted(set(by_group.get(gid, [])))}
                   for gid, g in sorted(k.groups.items())],
        "items": {str(i): {"qualified": items[i].qualified, "group": k.group_of(i), "runs": profiles[i].runs,
                           "measured": profiles[i].measured, "resolved": items[i].resolved} for i in sorted(items)},
        "dropped": [{"item": int(r.item), "problems": list(r.problems)} for r in records if r.outcome == "dropped"],
    }
