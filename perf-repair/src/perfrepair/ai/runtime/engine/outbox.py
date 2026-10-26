from __future__ import annotations

import re
from pathlib import Path

from ....dto.decision import OutboxRecord
from ....files import TEMP_SUFFIX, read_json, write_json, write_text

OUTBOXES, ACTIVE, LEGACY = "outbox", "active", "legacy"
RECORDS = "[0-9]*.json"
FINGERPRINT = re.compile(r"[0-9a-f]{12}")


class OutboxError(ValueError):
    pass


class Outbox:

    def __init__(self, directory: Path, fingerprint: str):
        self.directory = Path(directory)
        self.fingerprint = fingerprint

    def open(self) -> "Outbox":
        self.directory.mkdir(parents=True, exist_ok=True)
        for stale in self.directory.glob("*" + TEMP_SUFFIX):
            stale.unlink()
        return self

    def path(self, seq: int) -> Path:
        return self.directory / f"{seq:06d}.json"

    def read(self, seq: int) -> OutboxRecord:
        return OutboxRecord.from_json(read_json(self.path(seq)))

    def records(self) -> list[OutboxRecord]:
        records = []
        for n, path in enumerate(sorted(self.directory.glob(RECORDS)), 1):
            if path.name != self.path(n).name:
                raise ValueError(f"{path}: expected record {n}")
            record = OutboxRecord.from_json(read_json(path))
            if record.seq != n:
                raise ValueError(f"{path}: expected seq {n}, found {record.seq}")
            records.append(record)
        return records

    def append(self, record: OutboxRecord) -> OutboxRecord:
        write_json(self.path(record.seq), record.to_json(), durable=True, exclusive=True)
        return self.read(record.seq)


def _outbox(root: Path, fingerprint: str) -> Outbox:
    # legacy records sit flat in outbox/ from before prompts had fingerprints; they are never moved
    base = Path(root) / OUTBOXES
    return Outbox(base if fingerprint == LEGACY else base / fingerprint, fingerprint)


def active_fingerprint(root: Path) -> str | None:
    """The fingerprint `outbox/active` names; legacy for flat records without it; None before any record."""
    base = Path(root) / OUTBOXES
    marker = base / ACTIVE
    if not marker.exists():
        return LEGACY if any(base.glob(RECORDS)) else None
    name = marker.read_text().strip()
    if name != LEGACY and not FINGERPRINT.fullmatch(name):
        raise OutboxError(f"outbox_active_invalid: {marker} holds {name!r}")
    if not _outbox(root, name).directory.is_dir():
        raise OutboxError(f"outbox_missing: {marker} names {name}, which has no folder")
    return name


def active_outbox(root: Path) -> Outbox:
    """The run's outbox, for every reader; empty when nothing was ever committed."""
    return _outbox(root, active_fingerprint(root) or LEGACY)


def activate(root: Path, fingerprint: str) -> tuple[Outbox, Outbox | None]:
    """Opens the fingerprint's outbox and makes it active; returns it and the one it replaced."""
    if not FINGERPRINT.fullmatch(fingerprint):
        raise OutboxError(f"outbox_fingerprint_invalid: {fingerprint!r}")
    previous = active_fingerprint(root)
    outbox = _outbox(root, fingerprint).open()
    if previous == fingerprint:
        return outbox, None
    write_text(Path(root) / OUTBOXES / ACTIVE, fingerprint + "\n", durable=True)
    return outbox, None if previous is None else _outbox(root, previous)
