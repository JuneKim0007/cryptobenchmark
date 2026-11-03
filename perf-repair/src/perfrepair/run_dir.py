from __future__ import annotations

import re
from pathlib import Path

import yaml

from .dto import Measurements, PrimitiveRow, RunLog
from .dto.device import DeviceRecord
from .dto.used import UsedSet
from .dto.screen import Verdict, read_screen, read_screen_catalog, read_screen_review
from .files import read_json, read_yaml, sha256_file, write_text

MANIFEST, DEVICE = "manifest.yaml", "device.yaml"
ROWS, MEASUREMENTS, RUN_LOG, SITES = "rows.json", "measurements.json", "run_log.json", "sites.json"
PRIMITIVES = "primitives.tsv"
# the apps' items and the global.yaml that measures only them: device.filterByApps
USED, USED_CONFIG = "used.json", "used-global.yaml"
EVIDENCE, VERDICTS = "evidence.json", "verdicts.json"
APP, SCOPES, UNITS, DOSSIERS = "app.json", "scopes.json", "units.json", "dossiers.json"
REPLACE, REPLACEMENTS, EDITS, HARNESS = "replace", "replacements.json", "edits.json", "harness.yaml"
MEASURED, REPORT, REPORT_MD, SUMMARY, SUMMARY_MD = "measured", "report.json", "report.md", "summary.json", "summary.md"
FINISHED = "finished.json"
# cryptobenchmark's --harness layout under measured/: docs/results.md `scoped/`
SCOPED_PLAN, SCOPED_BENCHMARK = "scoped/scoped-plan.yaml", "scoped/benchmark.json"
GROUPING = "grouping"
# the run log: events.jsonl is the record; the .log files are views of it
LOG, EVENTS = "log", "log/events.jsonl"
SCREENING_AI_LOG, GROUPING_AI_LOG, BUG_LOG = "log/screening/ai.log", "log/grouping/ai.log", "log/bug.log"
CHARTER = "charter.json"
_APP_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def device_folders(root: Path) -> list[str]:
    """The finished devices of a results root: a folder without a manifest is a run that did not end."""
    root = Path(root)
    return sorted(p.name for p in root.iterdir() if (p / MANIFEST).is_file()) if root.is_dir() else []


def not_device_results(folder: Path) -> str:
    return f"not_device_results: {folder} has no {MANIFEST}; pass <root>/<device id>"


def app_dir(device: Path, name: str) -> Path:
    """<device>/<name>/: one app's files; the name is a single path segment."""
    if not _APP_NAME.fullmatch(name):
        raise ValueError(f"app name {name!r}: letters, digits, '.', '_' or '-', not starting with a symbol")
    return Path(device) / name


class AppPaths:
    """Files of one app under `<device>/<app>/`; `original/` and `patched/` hold only the files an edit changed."""

    def __init__(self, device: Path, app: str):
        self.app = app
        self.root = app_dir(device, app)

    sites = property(lambda self: self.root / SITES)
    facts = property(lambda self: self.root / APP)
    scopes = property(lambda self: self.root / SCOPES)
    units = property(lambda self: self.root / UNITS)
    dossiers = property(lambda self: self.root / DOSSIERS)
    replace = property(lambda self: self.root / REPLACE)
    replacements = property(lambda self: self.root / REPLACEMENTS)
    edits = property(lambda self: self.root / EDITS)
    original = property(lambda self: self.root / "original")
    patched = property(lambda self: self.root / "patched")
    alone_root = property(lambda self: self.root / "patched-alone")
    harness = property(lambda self: self.root / HARNESS)
    extracts = property(lambda self: self.root / "harness")
    measured = property(lambda self: self.root / MEASURED)
    scoped_plan = property(lambda self: self.root / MEASURED / SCOPED_PLAN)
    scoped_benchmark = property(lambda self: self.root / MEASURED / SCOPED_BENCHMARK)
    report = property(lambda self: self.root / REPORT)
    report_md = property(lambda self: self.root / REPORT_MD)
    finished = property(lambda self: self.root / FINISHED)

    def alone(self, unit: str) -> Path:
        """Files with only this unit's edits, for a unit applied in a function another applied unit shares."""
        return self.alone_root / unit


class GroupingPaths:

    def __init__(self, device: Path):
        self.root = Path(device) / GROUPING

    items = property(lambda self: self.root / "items.json")
    profiles = property(lambda self: self.root / "profiles.json")
    screen = property(lambda self: self.root / "screen.json")
    cursor = property(lambda self: self.root / "cursor.json")
    knowledge = property(lambda self: self.root / "knowledge.json")
    journal = property(lambda self: self.root / "journal.jsonl")
    errors = property(lambda self: self.root / "errors.jsonl")
    checks = property(lambda self: self.root / "checks.json")
    supervisor = property(lambda self: self.root / "supervisor.json")
    supervisor_journal = property(lambda self: self.root / "supervisor.journal.jsonl")
    supervisor_charter = property(lambda self: self.root / "supervisor.charter.json")
    groups = property(lambda self: self.root / "groups.json")
    interop_plan = property(lambda self: self.root / "interop_plan.yaml")
    interop = property(lambda self: self.root / "interop.yaml")
    classify = property(lambda self: self.root / "classify")
    classify_batches = property(lambda self: self.root / "classify" / "batches.json")
    classified = property(lambda self: self.root / "classify" / "classified.json")
    registry_candidates = property(lambda self: self.root / "registry-candidates.yaml")


def app_dirs(device: Path) -> list[Path]:
    """Device-level folders sit beside the apps, so an app's folder is the one holding app.json."""
    device = Path(device)
    return sorted(p for p in device.iterdir() if (p / APP).is_file()) if device.is_dir() else []


WORTHINESS_PREFIX = "worthiness-"


def worthiness(device: Path, mode: str) -> Path:
    return Path(device) / f"{WORTHINESS_PREFIX}{mode}"


def worthiness_modes(device: Path) -> list[str]:
    """The perfMode name of each worthiness folder that holds verdicts."""
    return sorted(p.name.removeprefix(WORTHINESS_PREFIX) for p in Path(device).glob(f"{WORTHINESS_PREFIX}*")
                  if (p / VERDICTS).is_file())


def load_rows(device: Path) -> list[PrimitiveRow]:
    return [PrimitiveRow.from_json(r) for r in read_json(Path(device) / ROWS)["rows"]]


def load_measurements(device: Path) -> Measurements:
    return Measurements.from_json(read_json(Path(device) / MEASUREMENTS))


def load_run_log(device: Path) -> RunLog:
    return RunLog.from_json(read_json(Path(device) / RUN_LOG))


def built(paths: GroupingPaths) -> dict:
    """The digests screen.json binds its verdicts to: items.json and profiles.json as they are on disk."""
    return {"items": sha256_file(paths.items), "profiles": sha256_file(paths.profiles)}


def load_screen(paths: GroupingPaths) -> dict[int, Verdict] | None:
    return read_screen(read_json(paths.screen)) if paths.screen.exists() else None


def load_screen_catalog(paths: GroupingPaths) -> dict | None:
    return read_screen_catalog(read_json(paths.screen)) if paths.screen.exists() else None


def load_screen_review(paths: GroupingPaths) -> str | None:
    """The classify outbox fingerprint screen.json was reviewed under; None when no review ran."""
    return read_screen_review(read_json(paths.screen)) if paths.screen.exists() else None


def load_device_record(device: Path) -> tuple[DeviceRecord | None, str | None]:
    """The record, or None and why: absent, or unreadable; either means every stage it would vouch for reruns."""
    path = Path(device) / DEVICE
    if not path.is_file():
        return None, f"no {DEVICE}"
    try:
        return DeviceRecord.from_json(read_yaml(path)), None
    except (ValueError, KeyError, TypeError, yaml.YAMLError) as e:
        return None, f"{DEVICE} unreadable ({e})"


def load_used(device: Path) -> UsedSet | None:
    """None without used.json: every item counts as used."""
    path = Path(device) / USED
    return UsedSet.from_json(read_json(path)) if path.is_file() else None


def write_device_record(device: Path, record: DeviceRecord) -> Path:
    return write_text(Path(device) / DEVICE, yaml.safe_dump(record.to_json(), sort_keys=False))
