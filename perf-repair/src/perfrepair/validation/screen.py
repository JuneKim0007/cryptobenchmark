from __future__ import annotations

from ..dto.grouping import Item
from ..dto.screen import STATUSES, UNKNOWN, Verdict, read_screen


def validate_screen(verdicts: dict[int, Verdict], items: list[Item]) -> list[str]:
    ids = {i.id for i in items}
    problems = [f"{n}: no verdict" for n in sorted(ids - set(verdicts))]
    problems += [f"{n}: verdict for no item" for n in sorted(set(verdicts) - ids)]
    for n, v in sorted(verdicts.items()):
        if v.status not in STATUSES:
            problems.append(f"{n}: status {v.status!r} is not one of {list(STATUSES)}")
        if not v.reason:
            problems.append(f"{n}: no reason")
        if v.status != UNKNOWN and not v.source:
            problems.append(f"{n}: {v.status} without a source")
    return problems


def validate_screen_document(doc: dict, items: list[Item]) -> list[str]:
    try:
        verdicts = read_screen(doc)
    except (KeyError, TypeError, ValueError) as e:
        return [f"screen.json does not parse: {e}"]
    return validate_screen(verdicts, items)
