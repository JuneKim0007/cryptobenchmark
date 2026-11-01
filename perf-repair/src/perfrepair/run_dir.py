from __future__ import annotations

import re
from pathlib import Path

from .dto import Measurements, PrimitiveRow, RunLog
from .files import read_json

ROWS, MEASUREMENTS, RUN_LOG, SITES = "rows.json", "measurements.json", "run_log.json", "sites.json"
EVIDENCE = "evidence.json"
APPS, APP, SCOPES, DOSSIERS = "apps", "app.json", "scopes.json", "dossiers.json"
_APP_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def app_dir(run: Path, name: str) -> Path:
    """apps/<name>/: one app's detect and scope outputs; the name is a single path segment."""
    if not _APP_NAME.fullmatch(name):
        raise ValueError(f"app name {name!r}: letters, digits, '.', '_' or '-', not starting with a symbol")
    return Path(run) / APPS / name


def app_dirs(run: Path) -> list[Path]:
    root = Path(run) / APPS
    return sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []


def worthiness(run: Path, mode: str) -> Path:
    return Path(run) / f"worthiness-{mode}"


def app(run: Path, name: str) -> Path:
    return Path(run) / APPS / name


def load_rows(run: Path) -> list[PrimitiveRow]:
    return [PrimitiveRow.from_json(r) for r in read_json(Path(run) / ROWS)["rows"]]


def load_measurements(run: Path) -> Measurements:
    return Measurements.from_json(read_json(Path(run) / MEASUREMENTS))


def load_run_log(run: Path) -> RunLog:
    return RunLog.from_json(read_json(Path(run) / RUN_LOG))
