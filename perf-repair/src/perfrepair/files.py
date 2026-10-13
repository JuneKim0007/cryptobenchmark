from __future__ import annotations

import json
import os
from pathlib import Path

import yaml

TEMP_SUFFIX = ".tmp"


def read_json(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def read_yaml(path: Path) -> dict:
    return yaml.safe_load(Path(path).read_text()) or {}


def read_document(path: Path) -> dict:
    return read_json(path) if Path(path).suffix == ".json" else read_yaml(path)


def write_json(path: Path, doc: dict, durable: bool = False, exclusive: bool = False) -> Path:
    path = Path(path)
    if exclusive and path.exists():
        raise FileExistsError(f"{path}: already written")
    tmp = path.with_name(path.name + TEMP_SUFFIX)
    with tmp.open("w") as f:
        json.dump(doc, f, indent=1)
        if durable:
            f.flush()
            os.fsync(f.fileno())
    os.replace(tmp, path)
    if durable:
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    return path
