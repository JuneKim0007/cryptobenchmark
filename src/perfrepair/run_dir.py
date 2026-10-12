"""The run directory: the name of every artifact in it, and how each is read back."""
from __future__ import annotations

from pathlib import Path

from .dto import Measurements, PrimitiveRow, RunLog
from .files import read_json

ROWS, MEASUREMENTS, RUN_LOG, SITES = "rows.json", "measurements.json", "run_log.json", "sites.json"
EVIDENCE = "evidence.json"


def worthiness(run: Path, mode: str) -> Path:
    return Path(run) / f"worthiness-{mode}"


def load_rows(run: Path) -> list[PrimitiveRow]:
    return [PrimitiveRow.from_json(r) for r in read_json(Path(run) / ROWS)["rows"]]


def load_measurements(run: Path) -> Measurements:
    return Measurements.from_json(read_json(Path(run) / MEASUREMENTS))


def load_run_log(run: Path) -> RunLog:
    return RunLog.from_json(read_json(Path(run) / RUN_LOG))
