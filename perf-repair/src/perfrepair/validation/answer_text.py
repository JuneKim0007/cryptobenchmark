from __future__ import annotations

NOT_BLANK = r"\S"


def or_empty(pattern: str) -> str:
    return f"^$|{pattern}"


def alias_pattern(prefix: str) -> str:
    return f"^{prefix}[1-9][0-9]*$"
