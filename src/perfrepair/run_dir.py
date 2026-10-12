"""The run directory: the name of every artifact in it, and how each is read back."""
from __future__ import annotations

from pathlib import Path

from .dto import Measurements, PrimitiveRow, RunLog, Verdicts
from .files import read_json

ROWS, MEASUREMENTS, RUN_LOG, SITES = "rows.json", "measurements.json", "run_log.json", "sites.json"
EVIDENCE = "evidence-{mode}.json"


def worthiness(mode: str) -> str:
    return f"worthiness-{mode}"


def state(run: Path, kind: str) -> Path:
    return Path(run) / f"{kind}.state.json"


def journal(run: Path, kind: str) -> Path:
    return Path(run) / f"{kind}.journal.jsonl"


def load_rows(run: Path) -> list[PrimitiveRow]:
    return [PrimitiveRow.from_json(r) for r in read_json(Path(run) / ROWS)["rows"]]


def load_measurements(run: Path) -> Measurements:
    return Measurements.from_json(read_json(Path(run) / MEASUREMENTS))


def load_run_log(run: Path) -> RunLog:
    return RunLog.from_json(read_json(Path(run) / RUN_LOG))



def load_verdicts(run: Path, mode: str) -> Verdicts:
    return Verdicts.from_json(read_json(state(run, worthiness(mode))))
