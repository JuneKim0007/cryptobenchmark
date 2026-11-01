"""Gate C of the worthiness decision: a reply against its group's evidence, in the aliases the model saw."""
from __future__ import annotations

from ...dto import GroupEvidence, Pair, Verdict
from ...dto.worthiness import DECISIONS
from ...result.modes import Mode
from ..json_reply import parse_object


def aliases(e: GroupEvidence) -> dict[str, str]:
    """M1..Mn: member ids contain the table's column separator."""
    return {f"M{n}": m for n, m in enumerate(e.members, 1)}


def check_reply(text: str, e: GroupEvidence, mode: Mode) -> tuple[dict | None, list[str]]:
    d, problems = parse_object(text)
    if d is None:
        return None, problems
    decision = d.get("decision")
    reason = d.get("reason").strip() if isinstance(d.get("reason"), str) else ""
    raw = d.get("pairs") if isinstance(d.get("pairs"), list) else None
    problems, pairs = [], []
    if decision not in DECISIONS:
        problems.append(f"decision {decision!r} is not one of {DECISIONS}")
    if not reason:
        problems.append("reason is empty")
    if raw is None:
        problems.append("pairs is not a list")
        raw = []
    if decision == "test" and not raw:
        problems.append("test names no pair")
    if decision == "skip" and raw:
        problems.append("skip names pairs; a skip has none")
    alias = aliases(e)
    metrics = [p for c in e.configurations for p in c.pairs]
    for i, p in enumerate(raw):
        if not isinstance(p, dict):
            problems.append(f"pairs[{i}] is not an object")
            continue
        why = p.get("reason").strip() if isinstance(p.get("reason"), str) else ""
        if p.get("from") not in alias or p.get("to") not in alias or p.get("from") == p.get("to"):
            problems.append(f"pairs[{i}]: {p.get('from')!r} -> {p.get('to')!r} is not two different members "
                            f"({', '.join(alias)})")
            continue
        a, b = alias[p["from"]], alias[p["to"]]
        if not why:
            problems.append(f"pairs[{i}]: reason is empty")
        judged = [(mode.judge(m), m) for m in metrics if m.fromItem == a and m.toItem == b]
        hits = [m for j, m in judged if j == "improves"]
        if not hits:
            why_not = "lacks the measurements" if any(j == "not_measured" for j, _ in judged) else "does not improve"
            problems.append(f"pairs[{i}]: {b} {why_not} on {a} under {mode.name} in any configuration")
            continue
        # the pair carries its best-supported configuration; a low level is reported, never refused
        best = max(hits, key=lambda m: -1.0 if m.pImprove is None else m.pImprove)
        pairs.append(Pair(a, b, why, best.pImprove, best.level))
    if problems:
        return None, problems
    return Verdict(e.groupId, mode.name, decision, reason, "llm", mode.proxy, tuple(pairs)).to_json(), []
