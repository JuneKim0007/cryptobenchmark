"""classify/classified.json: answers only for batched ids, allowed values, a reason each."""
from __future__ import annotations

from ..dto.classify import ANSWERS, Answer, Batch


def validate_classified(answers: dict[int, Answer], batches: list[Batch]) -> list[str]:
    ids = [i for b in batches for i in b.ids]
    problems = [f"batches: id {i} is in two batches" for i in sorted({i for i in ids if ids.count(i) > 1})]
    problems += [f"{k}: answer for an id no batch lists" for k in sorted(set(answers) - set(ids))]
    return problems + [p for k, a in sorted(answers.items()) for p in _answer_problems(k, a)]


def _answer_problems(k: int, a: Answer) -> list[str]:
    checks = ((a.id != k, f"answer names id {a.id}"),
              (a.answer not in ANSWERS, f"answer {a.answer!r} is not one of {list(ANSWERS)}"),
              (not a.reason, "no reason"))
    return [f"{k}: {text}" for failed, text in checks if failed]
