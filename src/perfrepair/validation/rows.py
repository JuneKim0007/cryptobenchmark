"""rows.json: unique ids, identity fields present, sizes positive."""
from __future__ import annotations

from collections import Counter

from ..dto import PrimitiveRow

IDENTITY = ("rowId", "type", "algorithm", "provider", "operation")


def validate_rows(rows: list[PrimitiveRow]) -> list[str]:
    problems = [f"rowId {rid} appears {n} times" for rid, n in Counter(r.rowId for r in rows).items() if n > 1]
    for r in rows:
        problems += [f"{r.rowId}: {f} is empty" for f in IDENTITY if not getattr(r, f)]
        problems += [f"{r.rowId}: {f} {getattr(r, f)!r} is not a positive integer"
                     for f in ("keySize", "inputSize")
                     if getattr(r, f) is not None and (not isinstance(getattr(r, f), int) or getattr(r, f) <= 0)]
    return problems
