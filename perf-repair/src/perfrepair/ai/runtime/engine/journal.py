from __future__ import annotations

import json
from pathlib import Path

from ....files import append_line


def append(path: Path, entry: dict) -> None:
    append_line(path, json.dumps(entry))


def count(path: Path) -> int:
    path = Path(path)
    return len(path.read_text().splitlines()) if path.exists() else 0


def read(path: Path) -> list[dict]:
    path = Path(path)
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
