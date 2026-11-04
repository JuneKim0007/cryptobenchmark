"""The device folder's layout: each artifact's name, the device, app, grouping, review and worthiness paths."""
from __future__ import annotations

import re
from pathlib import Path

MANIFEST, DEVICE = "manifest.yaml", "device.yaml"
ROWS, MEASUREMENTS, RUN_LOG, SITES = "rows.json", "measurements.json", "run_log.json", "sites.json"
PRIMITIVES = "primitives.tsv"
# the apps' items and the global.yaml that measures only them: device.filterByApps
USED, USED_CONFIG = "used.json", "used-global.yaml"
# device.bundled.fromApps: the catalog rows matched to the providers the apps ship, and the config that applies them
BUNDLED_SUGGESTIONS, BUNDLED_CONFIG = "bundled-suggestions.yaml", "bundled-global.yaml"
# the global.yaml whose run.metrics perfMode decided, when the base says otherwise
METRICS_CONFIG = "metrics-global.yaml"
EVIDENCE, VERDICTS = "evidence.json", "verdicts.json"
APP, SCOPES, UNITS, DOSSIERS = "app.json", "scopes.json", "units.json", "dossiers.json"
REPLACE, REPLACEMENTS, EDITS, HARNESS = "replace", "replacements.json", "edits.json", "harness.yaml"
MEASURED, REPORT, REPORT_MD, SUMMARY, SUMMARY_MD = "measured", "report.json", "report.md", "summary.json", "summary.md"
FINISHED = "finished.json"
# one guide run per device folder at a time; its record runs/run_<id>.json
LOCK, RUNS = ".lock", "runs"
# apps.targets resolved: every app the guide runs and every candidate it left out
TARGETS = "targets.yaml"
# cryptobenchmark's --harness layout under measured/: docs/results.md `scoped/`
SCOPED_PLAN, SCOPED_BENCHMARK = "scoped/scoped-plan.yaml", "scoped/benchmark.json"
GROUPING = "grouping"
# the run log: events.jsonl is the record; the .log files are views of it
LOG, EVENTS = "log", "log/events.jsonl"
APPS_INDEX = "apps-index.tsv"
STATUS_LOG, BUG_LOG = "log/status.log", "log/bug.log"
# rewritten whole each run, for people; no stage reads it back
PRIMITIVES_MISSING = "log/details/primitives_missing.yaml"
# cryptobenchmark's transcripts, one file per run: log/pipeline/<run id>.log
PIPELINE_LOGS = "log/pipeline"
# one file per model stage; screening's classify and grouping's supervisor apart from their stage's other turns
AI_SCREENING_LOG, AI_CLASSIFY_LOG, AI_GROUPING_LOG = "log/ai/screening.log", "log/ai/classify.log", "log/ai/grouping.log"
AI_SUPERVISOR_LOG, AI_WORTHINESS_LOG, AI_REPLACE_LOG = "log/ai/supervisor.log", "log/ai/worthiness.log", "log/ai/replace.log"
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


REVIEW = "review"


def review_sheet(device: Path) -> Path:
    return Path(device) / REVIEW / "decisions.tsv"


def review_score(device: Path) -> Path:
    return Path(device) / REVIEW / "score.json"


def review_stability(device: Path) -> Path:
    return Path(device) / REVIEW / "stability.json"


WORTHINESS_PREFIX = "worthiness-"


def worthiness(device: Path, mode: str) -> Path:
    return Path(device) / f"{WORTHINESS_PREFIX}{mode}"


def worthiness_modes(device: Path) -> list[str]:
    """The perfMode name of each worthiness folder that holds verdicts."""
    return sorted(p.name.removeprefix(WORTHINESS_PREFIX) for p in Path(device).glob(f"{WORTHINESS_PREFIX}*")
                  if (p / VERDICTS).is_file())
