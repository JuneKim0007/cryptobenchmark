"""EventSink: every perfrepair log record as one Event line in events.jsonl, then the view lines it renders to."""
from __future__ import annotations

import dataclasses
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from cryptobench.paths import RunTree
from cryptobench.paths import EVENTS
from ..dto.event import FINDING, LOG, Event
from ..files import append_line
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
        self.dropped = 0

    def open(self, run: str) -> None:
        self.folder, self.run, self.buffer, self.dropped = None, run, [], 0

    def close(self) -> None:
        self.folder, self.run, self.buffer, self.dropped = None, None, [], 0

    def bind(self, folder: Path) -> None:
        folder = Path(folder)
        # a folder that does not exist is an error the command reports; the log never creates it
        if self.run is None or folder == self.folder or not folder.is_dir():
            return
        self.folder = folder
        pending, self.buffer = self.buffer, []
        for event in pending:
            self._write(event)
        if self.dropped:
            self._notice("log_dropped", f"{self.dropped} records logged before the device folder was known were "
                                        f"dropped past the first {BUFFER_LIMIT}", {"dropped": self.dropped})
            self.dropped = 0

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
                else:
                    self.dropped += 1
                return
            self._write(event)
        except Exception:
            self.handleError(record)

    def _relative(self, value: str | None) -> str | None:
        prefix = f"{self.folder}/"
        return value[len(prefix):] if isinstance(value, str) and value.startswith(prefix) else value

    def _notice(self, code: str, detail: str, data: dict) -> None:
        """A warning the sink itself writes, a finding like terminate's; through logging it would re-enter the sink."""
        self._write(Event(timestamp(time.time()), self.run, "run", "log", FINDING, outcome="warn", detail=detail,
                          data={**data, "code": code, "action": "warn"}))

    def _write(self, event: Event) -> None:
        data = event.data if isinstance(event.data, dict) else {"data": event.data}
        if isinstance(data.get("files"), dict):
            data = {**data, "files": {self._relative(p): d for p, d in data["files"].items()}}
        event = dataclasses.replace(event, ref=self._relative(event.ref), data=data)
        # default=str: a value of a shape no writer planned is written as text, never lost with its event
        cut = [EVENTS] if append_line(RunTree(self.folder).log.events, json.dumps(event.to_json(), default=str)) else []
        for name, view in VIEWS:
            line = view(event)
            if line is not None and append_line(self.folder / name, line):
                cut.append(name)
        for name in cut:
            self._notice("append_repaired", f"{name} ended mid-line; a newline went before the next line", {"file": name})
