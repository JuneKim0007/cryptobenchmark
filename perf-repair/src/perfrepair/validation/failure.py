from __future__ import annotations


class ValidationFailed(Exception):
    def __init__(self, what: str, problems: list[str]):
        self.problems = problems
        super().__init__(f"{what}: {len(problems)} problem(s)\n" + "\n".join(f"- {p}" for p in problems))


def require(what: str, problems: list[str]) -> None:
    if problems:
        raise ValidationFailed(what, problems)
