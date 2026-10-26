from __future__ import annotations

from pathlib import Path

from ....dto.decision import OutboxRecord
from ....files import TEMP_SUFFIX, read_json, write_json


class Outbox:

    def __init__(self, directory: Path):
        self.directory = Path(directory)

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
        for n, path in enumerate(sorted(self.directory.glob("[0-9]*.json")), 1):
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
