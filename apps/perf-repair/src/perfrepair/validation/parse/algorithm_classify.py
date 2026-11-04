"""Gate C of algorithm-classify: one answer per listed id, an allowed value, a reason."""
from __future__ import annotations

from ...dto.classify import ANSWERS, Batch
from ..json_reply import parse_object


def _answer_problems(n: int, a, listed: set[int], seen: set[int]) -> list[str]:
    if not isinstance(a, dict):
        return [f"answers[{n}] is not an object"]
    ident, problems = a.get("id"), []
    if not isinstance(ident, int) or isinstance(ident, bool) or ident not in listed:
        problems.append(f"answers[{n}]: id {ident!r} is not one of the listed ids {sorted(listed)}")
    elif ident in seen:
        problems.append(f"answers[{n}]: id {ident} is answered twice")
    seen.add(ident)
    if a.get("answer") not in ANSWERS:
        problems.append(f"answers[{n}]: answer {a.get('answer')!r} is not one of {list(ANSWERS)}")
    if not isinstance(a.get("reason"), str) or not a["reason"].strip():
        problems.append(f"answers[{n}]: reason is empty")
    return problems


def check_reply(text: str, batch: Batch) -> tuple[dict | None, list[str]]:
    d, problems = parse_object(text)
    if d is None:
        return None, problems
    if not isinstance(d.get("answers"), list):
        return None, ["answers is not a list"]
    listed, seen = set(batch.ids), set()
    problems = [p for n, a in enumerate(d["answers"]) for p in _answer_problems(n, a, listed, seen)]
    problems += [f"id {i} has no answer" for i in sorted(listed - seen)]
    if problems:
        return None, problems
    return {"answers": [{"id": a["id"], "answer": a["answer"], "reason": a["reason"].strip()}
                        for a in sorted(d["answers"], key=lambda a: a["id"])]}, []
