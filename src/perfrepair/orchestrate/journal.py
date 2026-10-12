"""journal.jsonl: one line per agent call, appended and never rewritten; the audit trail and the
input to replay (validation/journal.py)."""
from __future__ import annotations

import json
from pathlib import Path


def append(path: Path, entry: dict) -> None:
    with Path(path).open("a") as f:
        f.write(json.dumps(entry) + "\n")


def read(path: Path) -> list[dict]:
    path = Path(path)
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
