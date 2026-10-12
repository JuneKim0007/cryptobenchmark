"""run_log.json: measured entries name only rows that exist; every other entry carries a reason."""
from __future__ import annotations

from ..dto import PrimitiveRow, RunLog


def validate_run_log(log: RunLog, rows: list[PrimitiveRow]) -> list[str]:
    known, problems = {r.rowId for r in rows}, []
    for e in log.entries:
        where = f"{e.status} {e.provider} {e.type} {e.algorithm}"
        if e.status == "measured" and (unknown := sorted(set(e.rowIds) - known)):
            problems.append(f"{where}: rows {unknown} are not in rows.json")
        if e.status != "measured" and not e.reason:
            problems.append(f"{where}: no reason")
        if e.occurrences < 1:
            problems.append(f"{where}: occurrences {e.occurrences}")
    return problems
