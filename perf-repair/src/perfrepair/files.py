from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .dto.document import DocumentKind

TEMP_SUFFIX = ".tmp"


def read_text(path: Path) -> str:
    return Path(path).read_text()


def read_json(path: Path) -> dict:
    return json.loads(read_text(path))


def read_yaml(path: Path) -> dict:
    return yaml.safe_load(Path(path).read_text()) or {}


def read_document(path: Path) -> dict:
    return read_json(path) if Path(path).suffix == ".json" else read_yaml(path)


def read_versioned(kind: DocumentKind, path: Path) -> dict:
    """The document at path, refused with kind's InputError unless its schemaVersion is one kind accepts."""
    return kind.check(read_document(path), path)


def json_text(doc: dict) -> str:
    return json.dumps(doc, indent=1)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def sha256_file(path: Path) -> str | None:
    """The digest of the file's bytes as written; None when it is absent."""
    path = Path(path)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def _ends_mid_line(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size == 0:
        return False
    with path.open("rb") as f:
        f.seek(-1, os.SEEK_END)
        return f.read(1) != b"\n"


def append_line(path: Path, line: str) -> bool:
    """One write of one whole line in append mode; True when the file ended mid-line (a crash cut its last line), so a
    newline went first and the cut line stays a line of its own."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    cut = _ends_mid_line(path)
    with path.open("a") as f:
        f.write(("\n" if cut else "") + line.rstrip("\n") + "\n")
    return cut


@dataclass(frozen=True)
class Jsonl:
    """records: (line number, value) of each whole line; cut: lines a crash cut short, skipped; bad: (line, error) of
    the others that do not parse; partial: the last line has no newline yet."""
    records: list[tuple[int, Any]]
    cut: list[int]
    bad: list[tuple[int, str]]
    partial: bool


CUT = object()


def jsonl_value(line: str) -> Any:
    """The line's value; CUT for a prefix of a JSON value, which a crash leaves: it fails only at its end, or in a string
    left open, which a whole written line never has; else ValueError."""
    try:
        return json.loads(line)
    except json.JSONDecodeError as e:
        at_end = e.pos >= len(line.rstrip()) or e.msg.startswith("Unterminated string")
        if line.lstrip().startswith(("{", "[")) and at_end:
            return CUT
        raise


def read_jsonl(path: Path) -> Jsonl:
    text = Path(path).read_text() if Path(path).is_file() else ""
    records, cut, bad = [], [], []
    for n, line in enumerate(text[:text.rfind("\n") + 1].splitlines(), 1):
        try:
            value = jsonl_value(line)
        except ValueError as e:
            bad.append((n, str(e)))
            continue
        (cut.append(n) if value is CUT else records.append((n, value)))
    return Jsonl(records, cut, bad, bool(text) and not text.endswith("\n"))


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


def write_text_making_parents(path: Path, text: str) -> Path:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return write_text(path, text)


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
