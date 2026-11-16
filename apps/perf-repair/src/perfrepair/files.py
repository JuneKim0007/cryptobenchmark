from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptobench.shared.document.document import DocumentKind, read_yaml
from cryptobench.shared.document.write import write_text


def read_text(path: Path) -> str:
    return Path(path).read_text()


def read_json(path: Path) -> dict:
    return json.loads(read_text(path))


def read_document(path: Path) -> dict:
    return read_json(path) if Path(path).suffix == ".json" else read_yaml(path)


def read_versioned(kind: DocumentKind, path: Path) -> dict:
    """The document at path, refused with kind's InputError unless its schemaVersion is one kind accepts."""
    return kind.check(read_document(path), path)


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


def write_text_making_parents(path: Path, text: str) -> Path:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return write_text(path, text)
