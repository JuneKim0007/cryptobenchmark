"""group-candidates.yaml: model answers in groups.yaml's row shape plus provenance, for a person to promote; written by report."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from ...catalog.groups import SCHEMA_VERSION, group_catalog, row_contracts
from ...dto.decision import OutboxRecord
from ...dto.grouping_state import Answer, Knowledge
from ...dto.grouping_output import Finding
from ...log import run_id

SOURCE = "model answers of grouping assign, unreviewed; a person promotes a row into catalog/groups.yaml"
MODEL, CATALOG = "model", "catalog"


def _stamps(path: Path) -> dict[tuple, dict]:
    """Run and date of decisions an earlier write already stamped: a rebuild keeps when and where each was made."""
    try:
        doc = yaml.safe_load(path.read_text()) if path.exists() else None
    except yaml.YAMLError:
        return {}
    rows = [r for rows in ((doc or {}).get("families") or {}).values() for r in rows]
    return {(r["provenance"]["outbox"], d["seq"]): {"run": d["run"], "date": d["date"]}
            for r in rows for d in r["provenance"]["decisions"]}


def candidates(kind, knowledge: Knowledge, records: list[OutboxRecord], findings: list[Finding], outbox: str | None,
               previous: Path) -> dict:
    by_key, stamps = {i.key: i for i in kind.askable()}, _stamps(previous)
    now = {"run": run_id(), "date": datetime.now(timezone.utc).date().isoformat()}
    rows: dict[str, dict] = {}
    for record in records:
        item = by_key.get(record.item)
        if item is None or record.outcome != "decided":
            continue
        target, verdict = Answer.from_json(record.decision).target, (kind.screen or {}).get(item.id)
        row = rows.setdefault(target, {"family": item.family, "items": [], "decisions": []})
        row["items"].append(item)
        row["decisions"].append({"item": item.qualified, "seq": record.seq, "model": str(record.agent),
                                 **stamps.get((outbox, record.seq), now), "reason": Answer.from_json(record.decision).reason,
                                 "rejectedTurns": list(record.problems),
                                 "canonical": verdict.canonical if verdict else None})
    families: dict[str, list] = {}
    for gid, row in sorted(rows.items()):
        members = [{"type": i.type, "name": d["canonical"] or i.name} for i, d in zip(row["items"], row["decisions"])]
        families.setdefault(row["family"], []).append({
            "id": gid, "description": knowledge.held(gid).description,
            "contracts": row_contracts([kind.profiles[i.id].signature for i in row["items"] if kind.profiles[i.id].signature]),
            "members": members,
            "provenance": {"source": CATALOG if group_catalog().variant_of(gid) else MODEL, "outbox": outbox,
                           "decisions": row["decisions"],
                           "checks": {"gateC": "accepted", "findings": [
                               {"kind": f.kind, "severity": f.severity, "detail": f.detail} for f in findings if f.group == gid]}}})
    return {"schemaVersion": SCHEMA_VERSION, "source": SOURCE, "families": families}
