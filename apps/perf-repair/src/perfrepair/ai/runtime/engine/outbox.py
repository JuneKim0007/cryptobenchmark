from __future__ import annotations

import re
from pathlib import Path

from ....dto.decision import OutboxRecord
from ....stop.halt import Coded
from ....dto.prompt import Charter
from ....files import TEMP_SUFFIX, read_json, write_json, write_text
from ....run_dir import CHARTER
from . import charter_file

OUTBOXES, ACTIVE = "outbox", "active"
RECORDS = "[0-9]*.json"
FINGERPRINT = re.compile(r"[0-9a-f]{12}")


class OutboxError(Coded):
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


class NoOutbox:
    """Nothing committed yet: reads as no records and has no folder."""
    fingerprint = None

    def records(self) -> list[OutboxRecord]:
        return []


def _outbox(root: Path, fingerprint: str) -> Outbox:
    return Outbox(Path(root) / OUTBOXES / fingerprint, fingerprint)


def active_fingerprint(root: Path) -> str | None:
    """The fingerprint `outbox/active` names; None before any record."""
    base = Path(root) / OUTBOXES
    marker = base / ACTIVE
    if not marker.exists():
        if any(base.glob(RECORDS)):
            raise OutboxError(f"outbox_unversioned: {base} holds records outside a fingerprint folder")
        return None
    name = marker.read_text().strip()
    if not FINGERPRINT.fullmatch(name):
        raise OutboxError(f"outbox_active_invalid: {marker} holds {name!r}")
    if not _outbox(root, name).directory.is_dir():
        raise OutboxError(f"outbox_missing: {marker} names {name}, which has no folder")
    return name


def active_outbox(root: Path) -> Outbox | NoOutbox:
    """The run's outbox, for every reader; NoOutbox when nothing was ever committed."""
    fingerprint = active_fingerprint(root)
    return NoOutbox() if fingerprint is None else _outbox(root, fingerprint)


def activate(root: Path, charter: Charter) -> tuple[Outbox, Outbox | None]:
    """Opens the charter's outbox, its charter.json written once or checked, and makes it active; returns it and the
    one it replaced."""
    fingerprint = charter.fingerprint
    if not FINGERPRINT.fullmatch(fingerprint):
        raise OutboxError(f"outbox_fingerprint_invalid: {fingerprint!r}")
    previous = active_fingerprint(root)
    outbox = _outbox(root, fingerprint).open()
    charter_file.record(outbox.directory / CHARTER, charter)
    if previous == fingerprint:
        return outbox, None
    write_text(Path(root) / OUTBOXES / ACTIVE, fingerprint + "\n", durable=True)
    return outbox, None if previous is None else _outbox(root, previous)
