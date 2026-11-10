"""Typed reads of a device folder's artifacts at the schema their readers know."""
from __future__ import annotations

from pathlib import Path

from cryptobench.paths import MANIFEST, GroupingTree, RunTree
from ..dto import Measurements, PrimitiveRow, RunLog
from ..dto.primitive import ROWS_DOC
from ..dto.screen import Verdict, read_screen, read_screen_catalog, read_screen_review
from ..dto.site import DOSSIERS_DOC, EDITS_DOC, SCOPES_DOC, SITES_DOC
from ..dto.upgrade import Upgrade, read_upgrades
from ..dto.used import UsedSet
from ..files import read_json, read_versioned, sha256_file


def not_device_results(folder: Path) -> str:
    return f"not_device_results: {folder} has no {MANIFEST}; pass <root>/<device id>"


def load_rows(device: Path) -> list[PrimitiveRow]:
    return [PrimitiveRow.from_json(r) for r in read_versioned(ROWS_DOC, RunTree(device).rows)["rows"]]


def load_measurements(device: Path) -> Measurements:
    return Measurements.from_json(read_json(RunTree(device).measurements))


def load_run_log(device: Path) -> RunLog:
    return RunLog.from_json(read_json(RunTree(device).run_log))


def built(paths: GroupingTree) -> dict:
    """The digests screen.json binds its verdicts to: items.json and profiles.json as they are on disk."""
    return {"items": sha256_file(paths.items), "profiles": sha256_file(paths.profiles)}


def _screen(paths: GroupingTree, reader):
    return reader(read_json(paths.screen)) if paths.screen.exists() else None


def load_screen(paths: GroupingTree) -> dict[int, Verdict] | None:
    return _screen(paths, read_screen)


def load_screen_catalog(paths: GroupingTree) -> dict | None:
    return _screen(paths, read_screen_catalog)


def load_screen_review(paths: GroupingTree) -> str | None:
    """The classify outbox fingerprint screen.json was reviewed under; None when no review ran."""
    return _screen(paths, read_screen_review)


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
    path = RunTree(device).used
    return UsedSet.from_json(read_json(path)) if path.is_file() else None

