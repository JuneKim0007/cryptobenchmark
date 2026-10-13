from __future__ import annotations

from ...files import read_yaml

import re
from collections import defaultdict
from pathlib import Path


from ...dto import LogEntry, PrimitiveRow, RunLog

# '<caseId>: <snake_code>[: detail]' — the id has no whitespace; the code has at least one underscore.
_ID_PREFIX = re.compile(r"^(?P<id>\S+?): (?P<rest>[a-z]+(?:_[a-z]+)+(?::.*)?)$", re.DOTALL)
_SNAKE = re.compile(r"^[a-z]+(?:_[a-z]+)*$")
_IDENTITY_HASH = re.compile(r"@[0-9a-f]{6,}\b")
_LONG_HEX = re.compile(r"\b[0-9a-f]{32,}\b")

NO_SAMPLES = "no_samples: prepared, but absent from benchmark.json (refused before the timer, or the run died)"


def split_case_id(reason: str) -> tuple[str | None, str]:
    m = _ID_PREFIX.match(reason)
    if m and not _SNAKE.match(m["id"]):
        return m["id"], m["rest"]
    return None, reason


def normalise_reason(reason: str | None) -> str | None:
    if reason is None:
        return None
    reason = _LONG_HEX.sub("…", _IDENTITY_HASH.sub("@…", str(reason)))
    return " ".join(reason.split())


def _yaml(path: Path | None) -> dict:
    return read_yaml(path) if path is not None else {}


def build_run_log(rows: list[PrimitiveRow], prepared: dict[str, dict] | None = None,
                  skipped_yaml: Path | None = None, inventory_yaml: Path | None = None) -> tuple[RunLog, int]:
    folded: dict[tuple, list[str | None]] = defaultdict(list)

    def add(status, stage, provider, type_, algorithm, reason, row_id=None):
        folded[(status, stage, provider, type_, algorithm, normalise_reason(reason))].append(row_id)

    for r in rows:
        add("measured", "benchmark", r.provider, r.type, r.algorithm, None, r.rowId)

    measured = {r.rowId for r in rows}
    for case_id, c in (prepared or {}).items():
        if case_id not in measured:
            add("unmeasured", "benchmark", c.get("provider"), c.get("type"), c.get("algorithm"), NO_SAMPLES, case_id)

    for s in _yaml(skipped_yaml).get("skipped") or []:
        case_id, reason = split_case_id(str(s.get("reason") or ""))
        add("skipped", s.get("stage"), s.get("provider"), s.get("type"), s.get("name") or s.get("algorithm"),
            reason or None, case_id)

    for provider, types in (_yaml(inventory_yaml).get("providers") or {}).items():
        for type_, algorithms in (types or {}).items():
            for algorithm, verdict in (algorithms or {}).items():
                if isinstance(verdict, dict) and verdict.get("runs") is False:
                    add("not_runnable", "trial", provider, type_, algorithm, verdict.get("reason"))

    entries = [LogEntry(*key, occurrences=len(ids), rowIds=tuple(sorted(i for i in ids if i)))
               for key, ids in folded.items()]
    return RunLog(entries), sum(len(ids) for ids in folded.values())
