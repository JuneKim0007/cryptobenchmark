"""Every file of one results folder <results root>/<device id>/, named once; the sections take a folder so a stage can hold just its own."""
from __future__ import annotations

import re
from pathlib import Path

from . import names as n

_APP_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


class Section:

    def __init__(self, root: Path | str):
        self.root = Path(root)


class Configuration(Section):
    effective = property(lambda self: self.root / n.EFFECTIVE)
    inventory = property(lambda self: self.root / n.INVENTORY)
    report = property(lambda self: self.root / n.CONFIG_REPORT)
    guide = property(lambda self: self.root / n.GUIDE)
    known_answers = property(lambda self: self.root / n.KNOWN_ANSWERS)


class Discovery(Section):
    facts = property(lambda self: self.root / n.FACTS)
    energy = property(lambda self: self.root / n.ENERGY_CAPABILITY)
    energy_preflight = property(lambda self: self.root / n.ENERGY_PREFLIGHT)
    rails_config = property(lambda self: self.energy_preflight / "rails.pbtx")
    idle_trace = property(lambda self: self.energy_preflight / "idle.pftrace")
    busy_trace = property(lambda self: self.energy_preflight / "busy.pftrace")
    manafa = property(lambda self: self.energy_preflight / n.MANAFA)

    def captures(self) -> list[Path]:
        return list(self.root.glob(n.CAPTURE_PATTERN))

    def trial(self, stamp: str) -> Path:
        return self.root / n.TRIAL_FORM.format(stamp)

    def requirements(self, stamp: str) -> Path:
        return self.root / n.REQUIREMENTS_FORM.format(stamp)


class Preparation(Section):
    prepared = property(lambda self: self.root / n.PREPARED)
    skipped = property(lambda self: self.root / n.SKIPPED)


class Measurement(Section):
    """A folder that measured: benchmark/, a process-N of it, or a pass."""

    json = property(lambda self: self.root / n.BENCHMARK_JSON)
    data = property(lambda self: self.root / n.BENCHMARK_DATA)
    clocks = property(lambda self: self.root / n.CLOCKS)
    thermal = property(lambda self: self.root / n.THERMAL)
    cpu_pins = property(lambda self: self.root / n.CPU_PINS)
    energy = property(lambda self: self.root / n.ENERGY_JSON)
    energy_dry = property(lambda self: self.root / n.ENERGY_DRY)
    traces = property(lambda self: self.root / n.TRACES)
    dry_trace = property(lambda self: self.root / n.TRACES / n.DRY_TRACE)
    manafa = property(lambda self: self.root / n.MANAFA)
    cases = property(lambda self: self.root / n.CASES)

    def process(self, repetition: int) -> Measurement:
        return Measurement(self.root / n.PROCESS_FORM.format(repetition))

    def case(self, case: str) -> Path:
        return self.cases / f"{case}.json"


class Analysis(Section):
    summary = property(lambda self: self.root / n.SUMMARY_MD)
    throughput = property(lambda self: self.root / n.THROUGHPUT_CHART)
    latency = property(lambda self: self.root / n.LATENCY_CHART)
    stability = property(lambda self: self.root / n.STABILITY_CHART)

    def metric_against_time(self, metric: str) -> Path:
        return self.root / f"{metric}-vs-time.png"


class Charts(Section):
    """chart/<run id>/ or the folder analysis.dir names."""

    summary = property(lambda self: self.root / n.SUMMARY_MD)
    data = property(lambda self: self.root / n.CHART_DATA)
    manifest = property(lambda self: self.root / n.MANIFEST)

    def metric_data(self, metric: str) -> Path:
        return self.root / f"chart-data-{metric}.json"

    def group(self, group_id: int, label: str) -> Path:
        return self.root / f"{group_id}-{label}"


class CheckFolder(Section):
    result = property(lambda self: self.root / n.CHECK_RESULT)
    preparation = property(lambda self: Preparation(self.root / n.PREPARATION))


class InteropFolder(Section):
    plan = property(lambda self: self.root / n.INTEROP_PLAN)
    result = property(lambda self: self.root / n.INTEROP_RESULT)


class Scoped(Section):
    plan = property(lambda self: self.root / n.SCOPED_PLAN_NAME)
    interop = property(lambda self: self.root / n.SCOPED_INTEROP)


class AppTree:
    """Files of one app under <device>/<app>/; original/ and patched/ hold only the files an edit changed."""

    def __init__(self, device: Path | str, app: str):
        self.app = app
        self.root = app_dir(device, app)

    sites = property(lambda self: self.root / n.SITES)
    facts = property(lambda self: self.root / n.APP)
    scopes = property(lambda self: self.root / n.SCOPES)
    units = property(lambda self: self.root / n.UNITS)
    dossiers = property(lambda self: self.root / n.DOSSIERS)
    replace = property(lambda self: self.root / n.REPLACE)
    replacements = property(lambda self: self.root / n.REPLACEMENTS)
    upgrade = property(lambda self: self.root / n.UPGRADE)
    upgrades = property(lambda self: self.root / n.UPGRADES)
    edits = property(lambda self: self.root / n.EDITS)
    original = property(lambda self: self.root / "original")
    patched = property(lambda self: self.root / "patched")
    alone_root = property(lambda self: self.root / "patched-alone")
    harness = property(lambda self: self.root / n.HARNESS)
    extracts = property(lambda self: self.root / "harness")
    checked = property(lambda self: self.root / n.CHECKED)
    scoped_plan = property(lambda self: self.root / n.CHECKED / n.SCOPED_PLAN)
    report = property(lambda self: self.root / n.APP_REPORT)
    report_md = property(lambda self: self.root / n.APP_REPORT_MD)
    finished = property(lambda self: self.root / n.FINISHED)

    @classmethod
    def at(cls, folder: Path | str) -> "AppTree":
        """The tree of an app folder known by its path."""
        folder = Path(folder)
        return cls(folder.parent, folder.name)

    def alone(self, unit: str) -> Path:
        """Files with only this unit's edits, for a unit applied in a function another applied unit shares."""
        return self.alone_root / unit


class GroupingTree:

    def __init__(self, device: Path | str):
        self.root = Path(device) / n.GROUPING

    items = property(lambda self: self.root / "items.json")
    profiles = property(lambda self: self.root / "profiles.json")
    screen = property(lambda self: self.root / "screen.json")
    cursor = property(lambda self: self.root / "cursor.json")
    knowledge = property(lambda self: self.root / "knowledge.json")
    checks = property(lambda self: self.root / "checks.json")
    groups = property(lambda self: self.root / "groups.json")
    interop_plan = property(lambda self: self.root / n.INTEROP_PLAN)
    interop = property(lambda self: self.root / n.INTEROP_RESULT)
    interop_pending = property(lambda self: self.root / "interop_pending.yaml")
    classify = property(lambda self: self.root / "classify")
    classify_batches = property(lambda self: self.root / "classify" / "batches.json")
    classified = property(lambda self: self.root / "classify" / "classified.json")
    registry_candidates = property(lambda self: self.root / "registry-candidates.yaml")
    group_candidates = property(lambda self: self.root / "group-candidates.yaml")


def app_dir(device: Path | str, name: str) -> Path:
    """<device>/<name>/: one app's files; the name is a single path segment."""
    if not _APP_NAME.fullmatch(name):
        raise ValueError(f"app name {name!r}: letters, digits, '.', '_' or '-', not starting with a symbol")
    return Path(device) / name


class Logs(Section):
    """The run log of a device folder."""

    events = property(lambda self: self.root.parent / n.EVENTS)
    status = property(lambda self: self.root.parent / n.STATUS_LOG)
    bug = property(lambda self: self.root.parent / n.BUG_LOG)
    primitives_missing = property(lambda self: self.root.parent / n.PRIMITIVES_MISSING)
    benchmark_coverage = property(lambda self: self.root.parent / n.BENCHMARK_COVERAGE)
    pipeline = property(lambda self: self.root.parent / n.PIPELINE_LOGS)

    def ai(self, job: str) -> Path:
        return self.root.parent / n.AI_LOGS / f"{job}.yaml"

    def pipeline_run(self, run: str) -> Path:
        return self.pipeline / f"{run}.log"


class Review(Section):
    decisions = property(lambda self: self.root / "decisions.tsv")
    score = property(lambda self: self.root / "score.json")


class RunTree:

    def __init__(self, root: Path | str):
        self.root = Path(root)

    name = property(lambda self: self.root.name)
    manifest = property(lambda self: self.root / n.MANIFEST)
    configuration = property(lambda self: Configuration(self.root / n.CONFIGURATION))
    discovery = property(lambda self: Discovery(self.root / n.DISCOVERY))
    preparation = property(lambda self: Preparation(self.root / n.PREPARATION))
    benchmark = property(lambda self: Measurement(self.root / n.BENCHMARK))
    analysis = property(lambda self: Analysis(self.root / n.ANALYSIS))
    charts = property(lambda self: self.root / n.CHART)
    check = property(lambda self: CheckFolder(self.root / n.CHECK))
    interop = property(lambda self: InteropFolder(self.root / n.INTEROP))
    scoped = property(lambda self: Scoped(self.root / n.SCOPED))
    scoped_plan_failed = property(lambda self: self.root / n.SCOPED_PLAN_FAILED)

    device = property(lambda self: self.root / n.DEVICE)
    rows = property(lambda self: self.root / n.ROWS)
    measurements = property(lambda self: self.root / n.MEASUREMENTS)
    run_log = property(lambda self: self.root / n.RUN_LOG)
    primitives = property(lambda self: self.root / n.PRIMITIVES)
    used = property(lambda self: self.root / n.USED)
    used_config = property(lambda self: self.root / n.USED_CONFIG)
    used_test_set = property(lambda self: self.root / n.USED_TEST_SET)
    bundled_suggestions = property(lambda self: self.root / n.BUNDLED_SUGGESTIONS)
    bundled_config = property(lambda self: self.root / n.BUNDLED_CONFIG)
    metrics_config = property(lambda self: self.root / n.METRICS_CONFIG)
    targets = property(lambda self: self.root / n.TARGETS)
    apps_index = property(lambda self: self.root / n.APPS_INDEX)
    summary = property(lambda self: self.root / n.SUMMARY)
    summary_md = property(lambda self: self.root / n.SUMMARY_MD)
    charter = property(lambda self: self.root / n.CHARTER)
    runs = property(lambda self: self.root / n.RUNS)
    lock = property(lambda self: self.root / n.LOCK)
    log = property(lambda self: Logs(self.root / n.LOG))
    grouping = property(lambda self: GroupingTree(self.root))
    review = property(lambda self: Review(self.root / n.REVIEW))

    def app(self, name: str) -> AppTree:
        return AppTree(self.root, name)

    def apps(self) -> list[Path]:
        """Device-level folders sit beside the apps, so an app's folder is the one holding app.json."""
        return sorted(p for p in self.root.iterdir() if (p / n.APP).is_file()) if self.root.is_dir() else []

    def run_record(self, run_id: str) -> Path:
        return self.runs / f"run_{run_id}.json"
