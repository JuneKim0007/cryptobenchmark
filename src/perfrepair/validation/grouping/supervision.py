"""A supervisor's answer for one family: well-formed findings that name only that family's groups and items,
with the arity each kind needs."""
from __future__ import annotations

import json

from ...grouping.supervise.schema import KINDS


def parse_review(text: str, groups: dict[str, list[int]]) -> tuple[list[dict] | None, list[str]]:
    try:
        d = json.loads(text)
    except json.JSONDecodeError as e:
        return None, [f"reply is not JSON: {e}"]
    findings = d.get("findings") if isinstance(d, dict) else None
    if not isinstance(findings, list):
        return None, ["findings is not a list"]
    members = {m for ms in groups.values() for m in ms}
    problems = []
    for n, f in enumerate(findings):
        where = f"findings[{n}]"
        if not isinstance(f, dict):
            problems.append(f"{where}: not an object")
            continue
        kind, gs, its = f.get("kind"), f.get("groups") or [], f.get("items") or []
        if kind not in KINDS:
            problems.append(f"{where}: kind {kind!r} is not one of {KINDS}")
        problems += [f"{where}: group {g!r} is not in this family" for g in gs if g not in groups]
        problems += [f"{where}: item {i!r} is not in this family" for i in its if i not in members]
        if kind == "merge" and len(set(gs)) < 2:
            problems.append(f"{where}: merge names fewer than two groups")
        if kind in ("split", "describe") and len(gs) != 1:
            problems.append(f"{where}: {kind} names exactly one group")
        if kind == "misplaced" and (len(its) < 1 or len(gs) != 2):
            problems.append(f"{where}: misplaced names the item(s), their group and the right group")
        if not str(f.get("reason") or "").strip():
            problems.append(f"{where}: reason is empty")
    return (findings if not problems else None), problems
