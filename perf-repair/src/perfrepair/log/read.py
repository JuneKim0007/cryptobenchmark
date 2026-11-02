"""events.jsonl read whole, or followed: only whole lines, so a line being written is read on the next poll."""
from __future__ import annotations

import json
from pathlib import Path

from ..dto.event import Event


def parse(line: str, number: int) -> Event:
    try:
        return Event.from_json(json.loads(line))
    except (TypeError, ValueError) as e:
        raise ValueError(f"events_unreadable: line {number}: {e}") from None


def read_events(path: Path) -> list[Event]:
    path = Path(path)
    if not path.is_file():
        return []
    text = path.read_text()
    whole = text[:text.rfind("\n") + 1]
    return [parse(line, n) for n, line in enumerate(whole.splitlines(), 1)]


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
            out.append(parse(raw, self.line))
        return out
