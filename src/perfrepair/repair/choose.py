"""Worthiness verdicts (the model's decision) joined to call sites: the replacement for each site, or none."""
from __future__ import annotations

from .candidates import Candidate


def choose(found: list[Candidate], verdicts_doc: dict) -> list[dict]:
    by_group = {v["groupId"]: v for v in verdicts_doc["verdicts"]}
    out = []
    for c in found:
        verdict = by_group.get(c.group or "")
        pairs = [p for p in (verdict or {}).get("pairs") or [] if p["from"] == c.item and p["to"] in c.alternatives]
        replace = verdict is not None and verdict["decision"] == "test" and bool(pairs)
        out.append({"site": c.to_json(), "decision": verdict["decision"] if verdict else "no_verdict",
                    "replacement": pairs[0]["to"] if replace else None,
                    "reason": pairs[0]["reason"] if replace else (verdict or {}).get("reason", "group has no verdict")})
    return out
