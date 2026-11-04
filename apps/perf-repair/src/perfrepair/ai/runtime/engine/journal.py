"""journal.jsonl: append, line count and read; audit only. A line a crash cut short keeps its own line number, so every
ref after it still points at its turn."""
from __future__ import annotations

import json
from pathlib import Path

from ....files import append_line, read_jsonl
from ....stop import terminate
from ....stop.halt import Coded


def append(path: Path, entry: dict) -> None:
    if append_line(path, json.dumps(entry)):
        terminate("append_repaired", "the file ended mid-line; a newline went before the next turn", stage="run",
                  step="journal", item=str(path))


def count(path: Path) -> int:
    path = Path(path)
    return len(path.read_text().splitlines()) if path.exists() else 0


def read(path: Path) -> list[dict]:
    found = read_jsonl(path)
    if found.bad:
        raise Coded(f"journal_unreadable: {path} line {found.bad[0][0]}: {found.bad[0][1]}")
    return [value for _, value in found.records]
