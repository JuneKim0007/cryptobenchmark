"""events.jsonl read whole, or followed: only whole lines, so a line being written is read on the next poll; a line a
crash cut short is skipped (files.read_jsonl)."""
from __future__ import annotations

from pathlib import Path

from cryptobench.coded import InputError
from ..dto.event import Event
from ..files import CUT, jsonl_value, read_jsonl


def _event(value, number: int) -> Event:
    try:
        return Event.from_json(value)
    except (TypeError, ValueError) as e:
        raise InputError(f"events_unreadable: line {number}: {e}") from None


def parse(line: str, number: int) -> Event | None:
    try:
        value = jsonl_value(line)
    except ValueError as e:
        raise InputError(f"events_unreadable: line {number}: {e}") from None
    return None if value is CUT else _event(value, number)


def read_events(path: Path) -> list[Event]:
    found = read_jsonl(path)
    if found.bad:
        number, error = found.bad[0]
        raise InputError(f"events_unreadable: line {number}: {error}")
    return [_event(value, n) for n, value in found.records]


class Follower:
    """New whole lines since the last poll; a file that shrank was replaced and is read again from its start."""

    def __init__(self, path: Path, from_start: bool):
        self.path, self.offset, self.line = Path(path), 0, 0
        if not from_start and self.path.is_file():
            self.offset = self.path.stat().st_size
            self.line = self.path.read_bytes().count(b"\n")

    def poll(self) -> list[Event]:
        if not self.path.is_file():
            return []
        if self.path.stat().st_size < self.offset:
            self.offset, self.line = 0, 0
        with self.path.open("rb") as f:
            f.seek(self.offset)
            chunk = f.read()
        whole = chunk[:chunk.rfind(b"\n") + 1]
        self.offset += len(whole)
        out = []
        for raw in whole.decode().splitlines():
            self.line += 1
            event = parse(raw, self.line)
            if event is not None:
                out.append(event)
        return out
