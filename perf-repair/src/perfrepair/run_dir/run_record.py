"""What a device folder says is done, and its one writer: runs/run_<id>.json, each <app>/finished.json, device.yaml."""
from __future__ import annotations

import json
import time
from pathlib import Path

import yaml

from ..dto.coded import InputError
from ..dto.device import DeviceRecord
from ..files import read_json, read_yaml, write_json, write_text
from .layout import DEVICE, REPORT, REPORT_MD, RUNS, AppPaths, app_dirs
from .lock import DeviceLock

OVERWRITE, RESUME, SKIP = "overwrite", "resume", "skip"
ON_EXISTING = (OVERWRITE, RESUME, SKIP)
RUNNING, DONE, FAILED, STOPPED = "running", "done", "failed", "stopped"
SCHEMA_VERSION = FINISHED_SCHEMA = 1
STAMP = "%Y%m%dT%H%M%SZ"


def load_device_record(device: Path) -> tuple[DeviceRecord | None, str | None]:
    """The record, or None and why: absent, or unreadable; either means every stage it would vouch for reruns."""
    path = Path(device) / DEVICE
    if not path.is_file():
        return None, f"no {DEVICE}"
    try:
        return DeviceRecord.from_json(read_yaml(path)), None
    except (ValueError, KeyError, TypeError, yaml.YAMLError) as e:
        return None, f"{DEVICE} unreadable ({e})"


def write_device_record(device: Path, record: DeviceRecord) -> Path:
    return write_text(Path(device) / DEVICE, yaml.safe_dump(record.to_json(), sort_keys=False), durable=True)


def drop_device_record(device: Path) -> None:
    (Path(device) / DEVICE).unlink(missing_ok=True)


def run_path(device: Path, run_id: str) -> Path:
    return Path(device) / RUNS / f"run_{run_id}.json"


def _finished(paths: AppPaths) -> dict | None:
    """None when absent or unreadable, so a cut or hand-edited file reruns the app instead of failing it every run."""
    try:
        doc = read_json(paths.finished)
    except (OSError, ValueError):
        return None
    ok = isinstance(doc, dict) and doc.get("schemaVersion") == FINISHED_SCHEMA and isinstance(doc.get("inputs"), dict)
    return doc if ok else None


def _stamp(device: Path) -> str:
    # a generated id is never an existing run's, so two runs in one second do not overwrite each other
    base = time.strftime(STAMP, time.gmtime())
    run_id, n = base, 1
    while run_path(device, run_id).exists():
        n += 1
        run_id = f"{base}-{n}"
    return run_id


def _read(path: Path) -> dict | None:
    try:
        doc = read_json(path)
    except (OSError, ValueError):
        return None
    return doc if isinstance(doc, dict) and doc.get("schemaVersion") == SCHEMA_VERSION else None


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class RunRecord:
    """One guide run on one device folder; holds the folder's lock until close()."""

    def __init__(self, device: Path, doc: dict, lock: DeviceLock):
        self.device, self.doc, self.lock = Path(device), doc, lock
        self.started: set[str] = set()

    @property
    def id(self) -> str:
        return self.doc["id"]

    @property
    def path(self) -> Path:
        return run_path(self.device, self.id)

    @classmethod
    def open(cls, device: Path, run_id: str | None = None, on_existing: str = OVERWRITE,
             digests: dict | None = None) -> RunRecord:
        """run_id None takes a new timestamp id; a named one that exists follows on_existing. device_busy, run_exists."""
        lock = DeviceLock.take(device)
        try:
            run_id = run_id or _stamp(device)
            path = run_path(device, run_id)
            kept = _read(path) if path.exists() else None
            if path.exists() and on_existing == SKIP:
                raise InputError(f"run_exists: run {run_id} has a record ({path}); run.onExisting skip runs nothing")
            if path.exists() and on_existing == OVERWRITE:
                cls._clear(device)
                kept = None
            doc = kept or {"schemaVersion": SCHEMA_VERSION, "id": run_id, "start": _now(), "apps": {}}
            record = cls(device, {**doc, "onExisting": on_existing, "digests": digests or {},
                                  "device": {"status": RUNNING}}, lock)
            record._write()
            return record
        except BaseException:
            lock.release()
            raise

    @staticmethod
    def _clear(device: Path) -> None:
        for folder in app_dirs(device):
            AppPaths(device, folder.name).finished.unlink(missing_ok=True)
        drop_device_record(device)

    def _write(self) -> None:
        self.doc["updated"] = _now()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        write_json(self.path, self.doc, durable=True)

    def device_done(self, status: str = DONE, step: str | None = None, reason: str = "") -> None:
        self.doc["device"] = {"status": status, **({"step": step, "reason": reason} if status != DONE else {})}
        self._write()

    def app_step(self, app: str, step: str) -> None:
        """The first step of an app this run: its done mark and its report go, so a stop leaves no stale one."""
        if app not in self.started:
            self.started.add(app)
            paths = AppPaths(self.device, app)
            for path in (paths.finished, paths.root / REPORT, paths.root / REPORT_MD):
                path.unlink(missing_ok=True)
        self.doc["apps"][app] = {"status": RUNNING, "step": step}
        self._write()

    def app_done(self, app: str, inputs: dict, outcome: str) -> None:
        """A terminal outcome: the same inputs on a later run need no step."""
        write_json(AppPaths(self.device, app).finished,
                   {"schemaVersion": FINISHED_SCHEMA, "inputs": inputs, "outcome": outcome}, durable=True)
        self.doc["apps"][app] = {**self.doc["apps"].get(app, {}), "status": DONE, "outcome": outcome}
        self._write()

    def app_failed(self, app: str, step: str, reason: str, status: str = FAILED) -> None:
        AppPaths(self.device, app).finished.unlink(missing_ok=True)
        self.doc["apps"][app] = {"status": status, "step": step, "reason": reason}
        self._write()

    def is_done(self, app: str, inputs: dict) -> bool:
        doc = _finished(AppPaths(self.device, app))
        # a JSON round trip, so a tuple in the inputs compares as the list the file holds
        return doc is not None and doc["inputs"] == json.loads(json.dumps(inputs))

    def app_reused(self, app: str) -> str:
        """The outcome the reused app reached when it was done."""
        outcome = (_finished(AppPaths(self.device, app)) or {}).get("outcome", "")
        self.doc["apps"][app] = {"status": DONE, "outcome": outcome, "reused": True}
        self._write()
        return outcome

    def close(self) -> None:
        self.lock.release()
