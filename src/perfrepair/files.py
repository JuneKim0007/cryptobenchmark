"""JSON documents on disk: read, and replace atomically so a crash never leaves half a file."""
from __future__ import annotations

import json
import os
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def write_json(path: Path, doc: dict) -> None:
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(doc, indent=1))
    os.replace(tmp, path)
