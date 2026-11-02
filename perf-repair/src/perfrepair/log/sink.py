"""EventSink: every perfrepair log record as one Event line in events.jsonl, then the view lines it renders to."""
from __future__ import annotations

import dataclasses
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from ..dto.event import LOG, Event
from ..files import append_line
from ..run_dir import EVENTS
from .emit import EVENT_ATTR
from .views import VIEWS

# records logged before the device folder is known; a command that never names one drops them
BUFFER_LIMIT = 10000
EXTRA_KEYS = ("code", "input", "source")


def timestamp(created: float) -> str:
    return datetime.fromtimestamp(created, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def to_event(record: logging.LogRecord, run: str) -> Event:
    fields = getattr(record, EVENT_ATTR, None)
    if fields is not None:
        return Event(timestamp(record.created), run, **fields)
    parts = record.name.split(".")
    stage = parts[1] if len(parts) > 1 else parts[0]
    return Event(timestamp(record.created), run, stage, ".".join(parts[2:]) or stage, LOG,
                 outcome=record.levelname.lower(), detail=record.getMessage(),
                 data={k: getattr(record, k) for k in EXTRA_KEYS if hasattr(record, k)})


class EventSink(logging.Handler):

    def __init__(self):
        super().__init__(logging.DEBUG)
        self.folder: Path | None = None
        self.run: str | None = None
        self.buffer: list[Event] = []

    def open(self, run: str) -> None:
        self.folder, self.run, self.buffer = None, run, []

    def close(self) -> None:
        self.folder, self.run, self.buffer = None, None, []

    def bind(self, folder: Path) -> None:
        folder = Path(folder)
        # a folder that does not exist is an error the command reports; the log never creates it
        if self.run is None or folder == self.folder or not folder.is_dir():
            return
        self.folder = folder
        pending, self.buffer = self.buffer, []
        for event in pending:
            self._write(event)

    def path(self, name: str) -> Path | None:
        return None if self.folder is None else self.folder / name

    def emit(self, record: logging.LogRecord) -> None:
        if self.run is None:
            return
        try:
            event = to_event(record, self.run)
            if self.folder is None:
                if len(self.buffer) < BUFFER_LIMIT:
                    self.buffer.append(event)
                return
            self._write(event)
        except Exception:
            self.handleError(record)

    def _relative(self, value: str | None) -> str | None:
        prefix = f"{self.folder}/"
        return value[len(prefix):] if isinstance(value, str) and value.startswith(prefix) else value

    def _write(self, event: Event) -> None:
        data = event.data
        if "files" in data:
            data = {**data, "files": {self._relative(p): d for p, d in data["files"].items()}}
        event = dataclasses.replace(event, ref=self._relative(event.ref), data=data)
        append_line(self.folder / EVENTS, json.dumps(event.to_json()))
        for name, view in VIEWS:
            line = view(event)
            if line is not None:
                append_line(self.folder / name, line)
