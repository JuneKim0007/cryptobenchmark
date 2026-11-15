"""json_text: a document as the JSON text its writers have always written; write_json, that text through the atomic write_text."""
from __future__ import annotations

import json
from pathlib import Path

from .write import write_text


def json_text(doc: dict) -> str:
    return json.dumps(doc, indent=1)


def write_json(path: Path, doc: dict, durable: bool = False, exclusive: bool = False) -> Path:
    return write_text(path, json_text(doc), durable, exclusive)
