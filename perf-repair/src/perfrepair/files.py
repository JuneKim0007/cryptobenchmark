from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import yaml

TEMP_SUFFIX = ".tmp"


def read_text(path: Path) -> str:
    return Path(path).read_text()


def read_json(path: Path) -> dict:
    return json.loads(read_text(path))


def read_yaml(path: Path) -> dict:
    return yaml.safe_load(Path(path).read_text()) or {}


def read_document(path: Path) -> dict:
    return read_json(path) if Path(path).suffix == ".json" else read_yaml(path)


def json_text(doc: dict) -> str:
    return json.dumps(doc, indent=1)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def sha256_file(path: Path) -> str | None:
    """The digest of the file's bytes as written; None when it is absent."""
    path = Path(path)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def append_line(path: Path, line: str) -> None:
    """One write of one whole line in append mode; a crash can leave only the last line partial, which readers refuse."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(line.rstrip("\n") + "\n")


def write_json(path: Path, doc: dict, durable: bool = False, exclusive: bool = False) -> Path:
    return write_text(path, json_text(doc), durable, exclusive)


def _staged(path: Path, text: str, durable: bool) -> Path:
    tmp = path.with_name(path.name + TEMP_SUFFIX)
    with tmp.open("w") as f:
        f.write(text)
        if durable:
            f.flush()
            os.fsync(f.fileno())
    return tmp


def write_texts(texts: list[tuple[Path, str]]) -> None:
    """Every file is staged before the first rename, so a failure while staging leaves every old file; renames run in order."""
    staged = [(_staged(Path(p), t, False), Path(p)) for p, t in texts]
    for tmp, path in staged:
        os.replace(tmp, path)


def write_text(path: Path, text: str, durable: bool = False, exclusive: bool = False) -> Path:
    path = Path(path)
    if exclusive and path.exists():
        raise FileExistsError(f"{path}: already written")
    os.replace(_staged(path, text, durable), path)
    if durable:
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    return path
