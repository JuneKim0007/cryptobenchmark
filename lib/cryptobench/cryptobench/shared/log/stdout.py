"""The labelled lines other programs read from a run's output: a label padded to one column, then its value."""
from __future__ import annotations

RESULTS, WROTE, IDENTITY, TOOK = (f"{label:<11}" for label in ("results:", "wrote:", "identity:", "took:"))
ERROR = "error: "


def line(label: str, value) -> str:
    return f"{label}{value}"


def say(label: str, value, file=None) -> None:
    print(line(label, value), file=file)


def last(label: str, lines) -> str | None:
    """The value of the last line that starts with label, None without one."""
    found = [text[len(label):].strip() for text in lines if text.startswith(label)]
    return found[-1] if found else None
