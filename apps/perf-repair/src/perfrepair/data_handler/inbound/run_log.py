from __future__ import annotations

from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.results import skipped

import re
from collections import defaultdict
from pathlib import Path


from ...dto import LogEntry, PrimitiveRow, RunLog, run_log

_IDENTITY_HASH = re.compile(r"@[0-9a-f]{6,}\b")
_LONG_HEX = re.compile(r"\b[0-9a-f]{32,}\b")

NO_REQUIRED_METRIC = "no_required_metric: in benchmark.json without runs of a required metric; left out of the rows"
VARIANT_UNREPAIRED = "variant_unrepaired: measures a path no call site pattern maps to; left out of the rows"
NO_SAMPLES = "no_samples: prepared, but absent from benchmark.json (refused before the timer, or the run died)"


def normalise_reason(reason: str | None) -> str | None:
    if reason is None:
        return None
    reason = _LONG_HEX.sub("…", _IDENTITY_HASH.sub("@…", str(reason)))
    return " ".join(reason.split())


def _yaml(path: Path | None) -> dict:
    return read_yaml(path) if path is not None else {}


def _unmeasured(add, rows: list[PrimitiveRow], prepared: dict[str, dict], lacking: dict[str, dict], unrepaired: list[PrimitiveRow]) -> None:
    """A case benchmark.json has without a required metric's runs, or on a path no pattern maps to, says so; a prepared one it lacks is no_samples."""
    for case_id, c in lacking.items():
        add(run_log.UNMEASURED, "benchmark", c.get("provider"), c.get("type"), c.get("algorithm"), NO_REQUIRED_METRIC, case_id)
    for r in unrepaired:
        add(run_log.UNMEASURED, "benchmark", r.provider, r.type, r.algorithm, VARIANT_UNREPAIRED, r.rowId)
    measured = {r.rowId for r in rows} | set(lacking) | {r.rowId for r in unrepaired}
    for case_id, c in prepared.items():
        if case_id not in measured:
            add(run_log.UNMEASURED, "benchmark", c.get("provider"), c.get("type"), c.get("algorithm"), NO_SAMPLES, case_id)


def build_run_log(rows: list[PrimitiveRow], prepared: dict[str, dict] | None = None,
                  skipped_yaml: Path | None = None, inventory_yaml: Path | None = None,
                  lacking: dict[str, dict] | None = None, unrepaired: list[PrimitiveRow] = ()) -> tuple[RunLog, int]:
    folded: dict[tuple, list[str | None]] = defaultdict(list)

    def add(status, stage, provider, type_, algorithm, reason, row_id=None):
        folded[(status, stage, provider, type_, algorithm, normalise_reason(reason))].append(row_id)

    for r in rows:
        add(run_log.MEASURED, "benchmark", r.provider, r.type, r.algorithm, None, r.rowId)
    _unmeasured(add, rows, prepared or {}, lacking or {}, list(unrepaired))

    for s in skipped.records(_yaml(skipped_yaml)):
        reason = ": ".join(str(part) for part in (s.get("code"), s.get("reason")) if part)
        add(run_log.SKIPPED, s.get("stage"), s.get("provider"), s.get("type"), s.get("name"), reason or None, s.get("caseId"))

    for provider, types in (_yaml(inventory_yaml).get("providers") or {}).items():
        for type_, algorithms in (types or {}).items():
            for algorithm, verdict in (algorithms or {}).items():
                if isinstance(verdict, dict) and verdict.get("runs") is False:
                    add(run_log.NOT_RUNNABLE, "trial", provider, type_, algorithm, verdict.get("reason"))

    entries = [LogEntry(*key, occurrences=len(ids), rowIds=tuple(sorted(i for i in ids if i)))
               for key, ids in folded.items()]
    return RunLog(entries), sum(len(ids) for ids in folded.values())
