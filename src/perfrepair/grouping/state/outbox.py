"""outbox/: one file per decided item, the only record of decisions.

A record is written to a temp file, flushed to disk, renamed into place and the directory flushed, so
after a crash a record either exists whole or not at all; a temp file left behind is discarded on open.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from ...dto.grouping_state import OutboxRecord

TEMP_PREFIX = ".tmp-"


class Outbox:

    def __init__(self, directory: Path):
        self.directory = Path(directory)

    def open(self) -> "Outbox":
        self.directory.mkdir(parents=True, exist_ok=True)
        for stale in self.directory.glob(TEMP_PREFIX + "*"):
            stale.unlink()
        return self

    def _path(self, seq: int) -> Path:
        return self.directory / f"{seq:06d}.json"

    def records(self) -> list[OutboxRecord]:
        """Every record in sequence order; a gap or an unreadable record is refused, never skipped."""
        records = []
        for n, path in enumerate(sorted(self.directory.glob("[0-9]*.json")), 1):
            record = OutboxRecord.from_json(json.loads(path.read_text()))
            if record.seq != n or path.name != self._path(n).name:
                raise ValueError(f"{path}: expected record {n}, found seq {record.seq}")
            records.append(record)
        return records

    def append(self, record: OutboxRecord) -> Path:
        target = self._path(record.seq)
        if target.exists():
            raise FileExistsError(f"{target}: record {record.seq} already written")
        temp = self.directory / f"{TEMP_PREFIX}{record.seq:06d}.json"
        with temp.open("w") as f:
            json.dump(record.to_json(), f, indent=1)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, target)
        directory = os.open(self.directory, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        return target
