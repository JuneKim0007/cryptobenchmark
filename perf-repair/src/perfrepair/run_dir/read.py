"""Typed reads of a device folder's artifacts at the schema their readers know; device.yaml written."""
from __future__ import annotations

from pathlib import Path

import yaml

from ..dto import Measurements, PrimitiveRow, RunLog
from ..dto.device import DeviceRecord
from ..dto.primitive import ROWS_SCHEMA_VERSION
from ..dto.screen import Verdict, read_screen, read_screen_catalog, read_screen_review
from ..dto.site import (
    DOSSIERS_SCHEMA_VERSION,
    EDITS_SCHEMA_VERSION,
    SCOPES_SCHEMA_VERSION,
    SITES_SCHEMA_VERSION,
)
from ..dto.used import UsedSet
from ..files import read_json, read_yaml, sha256_file, write_text
from .layout import DEVICE, MEASUREMENTS, ROWS, RUN_LOG, USED, GroupingPaths


def load_rows(device: Path) -> list[PrimitiveRow]:
    doc = read_json(Path(device) / ROWS)
    if doc.get("schemaVersion") != ROWS_SCHEMA_VERSION:
        raise ValueError(f"rows schemaVersion {doc.get('schemaVersion')} is not {ROWS_SCHEMA_VERSION}")
    return [PrimitiveRow.from_json(r) for r in doc["rows"]]


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


def load_device_record(device: Path) -> tuple[DeviceRecord | None, str | None]:
    """The record, or None and why: absent, or unreadable; either means every stage it would vouch for reruns."""
    path = Path(device) / DEVICE
    if not path.is_file():
        return None, f"no {DEVICE}"
    try:
        return DeviceRecord.from_json(read_yaml(path)), None
    except (ValueError, KeyError, TypeError, yaml.YAMLError) as e:
        return None, f"{DEVICE} unreadable ({e})"


def versioned(path: Path, version: int) -> dict:
    """An app artifact at the schema its readers know; another is schema_version, never a field read as missing."""
    doc = read_json(path)
    if doc.get("schemaVersion") != version:
        raise ValueError(f"schema_version: {path} schemaVersion {doc.get('schemaVersion')!r} is not {version}; "
                         "rerun the step that writes it")
    return doc


def read_scopes(path: Path) -> dict:
    return versioned(path, SCOPES_SCHEMA_VERSION)


def read_sites(path: Path) -> dict:
    return versioned(path, SITES_SCHEMA_VERSION)


def read_edits(path: Path) -> dict:
    return versioned(path, EDITS_SCHEMA_VERSION)


def read_dossiers(path: Path) -> dict:
    return versioned(path, DOSSIERS_SCHEMA_VERSION)


def load_used(device: Path) -> UsedSet | None:
    """None without used.json: every item counts as used."""
    path = Path(device) / USED
    return UsedSet.from_json(read_json(path)) if path.is_file() else None


def write_device_record(device: Path, record: DeviceRecord) -> Path:
    return write_text(Path(device) / DEVICE, yaml.safe_dump(record.to_json(), sort_keys=False))
