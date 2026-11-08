from __future__ import annotations

NOT_BLANK = r"\S"


def or_empty(pattern: str) -> str:
    return f"^$|{pattern}"
