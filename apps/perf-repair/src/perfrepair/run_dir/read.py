"""Typed reads of a device folder's artifacts at the schema their readers know."""
from __future__ import annotations

from pathlib import Path

from ..dto import Measurements, PrimitiveRow, RunLog
from ..dto.primitive import ROWS_DOC
from ..dto.screen import Verdict, read_screen, read_screen_catalog, read_screen_review
from ..dto.site import DOSSIERS_DOC, EDITS_DOC, SCOPES_DOC, SITES_DOC
from ..dto.upgrade import Upgrade, read_upgrades
from ..dto.used import UsedSet
from ..files import read_json, read_versioned, sha256_file
from .layout import MEASUREMENTS, ROWS, RUN_LOG, USED, GroupingPaths


def load_rows(device: Path) -> list[PrimitiveRow]:
    return [PrimitiveRow.from_json(r) for r in read_versioned(ROWS_DOC, Path(device) / ROWS)["rows"]]


def load_measurements(device: Path) -> Measurements:
    return Measurements.from_json(read_json(Path(device) / MEASUREMENTS))


def load_run_log(device: Path) -> RunLog:
    return RunLog.from_json(read_json(Path(device) / RUN_LOG))


def built(paths: GroupingPaths) -> dict:
    """The digests screen.json binds its verdicts to: items.json and profiles.json as they are on disk."""
    return {"items": sha256_file(paths.items), "profiles": sha256_file(paths.profiles)}


def load_screen(paths: GroupingPaths) -> dict[int, Verdict] | None:
    return read_screen(read_json(paths.screen)) if paths.screen.exists() else None


def load_screen_catalog(paths: GroupingPaths) -> dict | None:
    return read_screen_catalog(read_json(paths.screen)) if paths.screen.exists() else None


def load_screen_review(paths: GroupingPaths) -> str | None:
    """The classify outbox fingerprint screen.json was reviewed under; None when no review ran."""
    return read_screen_review(read_json(paths.screen)) if paths.screen.exists() else None


def read_scopes(path: Path) -> dict:
    return read_versioned(SCOPES_DOC, path)


def read_sites(path: Path) -> dict:
    return read_versioned(SITES_DOC, path)


def read_edits(path: Path) -> dict:
    return read_versioned(EDITS_DOC, path)


def load_upgrades(path: Path) -> list[Upgrade]:
    """What each broken use became; none before the upgrade step ran."""
    return read_upgrades(read_json(path)) if Path(path).is_file() else []


def read_dossiers(path: Path) -> dict:
    return read_versioned(DOSSIERS_DOC, path)


def load_used(device: Path) -> UsedSet | None:
    """None without used.json: every item counts as used."""
    path = Path(device) / USED
    return UsedSet.from_json(read_json(path)) if path.is_file() else None

