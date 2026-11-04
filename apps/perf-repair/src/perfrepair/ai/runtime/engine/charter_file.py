"""charter.json of an outbox: written once, checked on every later open, its fingerprint recomputed by the validator."""
from __future__ import annotations

from pathlib import Path

from ....dto.charter import charter_document, read_charter
from ....stop.halt import Coded
from ....dto.prompt import Charter
from ....files import read_json, write_json


class CharterMismatch(Coded):
    pass


def _hashed(doc: dict) -> dict:
    # where a prompt was read from is recorded, not compared: the same text from another file is the same charter
    return {k: ({n: v for n, v in doc[k].items() if n != "source"} if k in ("system", "correction") else doc[k])
            for k in doc}


def record(path: Path, charter: Charter) -> None:
    path, doc = Path(path), charter_document(charter)
    if not path.exists():
        write_json(path, doc, durable=True)
        return
    try:
        same = _hashed(read_json(path)) == _hashed(doc)
    except (KeyError, TypeError, ValueError):
        same = False
    if not same:
        raise CharterMismatch(f"charter_mismatch: {path} does not hold the charter {charter.fingerprint}")


def inputs(path: Path) -> str:
    """The run inputs of a recorded charter; none when it has no charter.json."""
    path = Path(path)
    return read_json(path)["inputs"] if path.is_file() else ""


def problems(path: Path, fingerprint: str) -> list[str]:
    """What is wrong with the charter.json that should hash to fingerprint."""
    path = Path(path)
    if not path.is_file():
        return [f"charter_missing: {path}"]
    try:
        found = read_charter(read_json(path)).fingerprint
    except (KeyError, TypeError, ValueError) as e:
        return [f"{path} does not parse: {e}"]
    return [] if found == fingerprint else [f"charter_mismatch: {path} hashes to {found}, not {fingerprint}"]
