"""journal.jsonl: one line per model turn, appended and never rewritten. Audit only: state is projected
from the outbox, never from here."""
from __future__ import annotations

import json
from pathlib import Path


def append(path: Path, entry: dict) -> None:
    with Path(path).open("a") as f:
        f.write(json.dumps(entry) + "\n")


def read(path: Path) -> list[dict]:
    path = Path(path)
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
