"""The one tracking reader: what a role's run reads and writes, heard from the interpreter's own file events, so every
loader of every role goes through it and none can go around it. `role_run` opens it; `decide` stamps each journal line."""
from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from ....catalog.role_contracts import CATALOG, RoleContract, role_contracts
from ....files import TEMP_SUFFIX, read_json, sha256_file, write_json
from ....run_dir import ROLE_WRITES
from ....stop.halt import Coded

CATALOG_DIR = CATALOG.parent
PREFIX = CATALOG_DIR.name + "/"


class MissingInput(Coded):
    pass


class RoleRun:

    def __init__(self, contract: RoleContract, device: Path):
        self.contract, self.device, self.charter = contract, os.path.realpath(device), None
        self.inputs: dict[tuple[str, str], None] = {}
        self.written: set[str] = set()
        self.hearing = True

    def name_of(self, path) -> str | None:
        """Its name under the device folder or the catalog; anything else is no input of a run."""
        if not isinstance(path, (str, os.PathLike)):
            return None
        full = os.path.realpath(path)
        if full.startswith(self.device + os.sep):
            return os.path.relpath(full, self.device)
        return PREFIX + os.path.relpath(full, CATALOG_DIR) if full.startswith(f"{CATALOG_DIR}{os.sep}") else None

    def read(self, path) -> None:
        name = self.name_of(path)
        if name is None or self.contract.bookkeeping(name):
            return
        self.hearing = False
        try:
            digest = sha256_file(path)
        except OSError:
            digest = None
        finally:
            self.hearing = True
        if digest is not None:
            self.inputs[(name, digest)] = None

    def wrote(self, path) -> None:
        name = self.name_of(path)
        if name is not None and not name.endswith(TEMP_SUFFIX):
            self.written.add(name)

    def record(self) -> None:
        """writes.json: what this charter's runs wrote, for the replay."""
        if self.charter is None:
            return
        path = Path(self.device) / self.contract.folder / ROLE_WRITES
        before = read_json(path) if path.is_file() else {}
        kept = before.get("files", []) if before.get("charter") == self.charter else []
        write_json(path, {"role": self.contract.role, "charter": self.charter, "files": sorted({*kept, *self.written})})


_current: ContextVar[RoleRun | None] = ContextVar("role_run", default=None)


def _heard(event: str, args: tuple) -> None:
    if event not in ("open", "os.rename", "os.remove"):
        return
    run = _current.get()
    if run is None or not run.hearing:
        return
    if event == "os.rename":
        run.wrote(args[1])
    elif event == "os.remove":
        run.wrote(args[0])
    elif not isinstance(args[2], int) or args[2] & os.O_ACCMODE == os.O_RDONLY:  # an open with no flags is a read
        run.read(args[0])
    else:
        run.wrote(args[0])


# an audit hook lives as long as the process; with no role run open it returns at once
sys.addaudithook(_heard)


def _found(device: Path, pattern: str) -> list[Path]:
    if pattern.startswith(PREFIX):
        return [p for p in [CATALOG_DIR.parent / pattern] if p.is_file()]
    return [p for p in Path(device).glob(pattern) if p.is_file()]


@contextmanager
def role_run(role: str, device: Path, **names):
    """A role's whole run; refused before any call when a required input is missing. A required catalog counts as read
    even when a cache already holds it."""
    contract = role_contracts()[role].bind(**names)
    missing = [p for p in contract.required if not _found(device, p)]
    if missing:
        raise MissingInput(f"missing_input: {role} needs {', '.join(missing)} under {device}")
    run = RoleRun(contract, Path(device))
    for pattern in contract.required:
        for path in _found(device, pattern) if pattern.startswith(PREFIX) else ():
            run.read(path)
    token = _current.set(run)
    try:
        yield run
    finally:
        _current.reset(token)
        run.record()


def opened(fingerprint: str) -> None:
    """The charter the open role run asks under."""
    run = _current.get()
    if run is not None:
        run.charter = fingerprint


def stamp() -> dict:
    """What a journal line carries: the role and each {file, digest} read so far; nothing outside a role run."""
    run = _current.get()
    if run is None:
        return {}
    return {"role": run.contract.role, "inputs": [{"file": f, "digest": d} for f, d in sorted(run.inputs)]}
