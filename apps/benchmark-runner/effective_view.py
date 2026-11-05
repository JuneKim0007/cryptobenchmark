"""Reading effective.yaml the way a run needs it: the settings, with what the run noticed joined back from report.yaml."""
import pathlib

import yaml

from failure import fail

CASE_ISOLATION = "case"
ISOLATIONS = (CASE_ISOLATION, "run")
DEFAULT_ISOLATION = CASE_ISOLATION
SCOPED_REPETITIONS = 3   # RunSettings.scopedRepetitions


def read(effective_file):
    effective = pathlib.Path(effective_file)
    document = yaml.safe_load(effective.read_text()) or {}
    report_file = effective.parent / "report.yaml"
    report = (yaml.safe_load(report_file.read_text()) or {}) if report_file.is_file() else {}
    return {
        "document": document,
        "warnings": report.get("warnings") or [],
        "skipped": report.get("skipped") or [],
    }


def entry_count(document):
    return sum(len(names) for types in (document.get("providers") or {}).values() for names in types.values())


def metrics(document):
    listed = (document.get("run") or {}).get("metrics")
    if not listed:
        fail("missing_field: run.metrics in effective.yaml")
    return listed


def isolation(document):
    chosen = (document.get("run") or {}).get("isolation", DEFAULT_ISOLATION)
    if chosen not in ISOLATIONS:
        fail(f"invalid: run.isolation {chosen}, expected one of [{', '.join(ISOLATIONS)}]")
    return chosen


def throttle_sleep(document):
    """None keeps Jetpack's own sleep; RunSettings already refused a negative value."""
    return (document.get("run") or {}).get("thermalThrottleSleepSeconds")


def case_cooldown(document):
    return (document.get("run") or {}).get("caseCooldownSeconds") or 0


def thermal_gate(document):
    """run.thermalGate as :config validated it, or None when absent or enabled false."""
    gate = (document.get("run") or {}).get("thermalGate")
    return gate if gate and gate.get("enabled", True) else None


def _repetitions(document, key, default):
    repetitions = (document.get("run") or {}).get(key, default)
    if type(repetitions) is not int or repetitions < 1:
        fail(f"not_positive: {key} {repetitions}")
    return repetitions


def scoped_repetitions(document):
    return _repetitions(document, "scopedRepetitions", SCOPED_REPETITIONS)


def process_repetitions(document):
    return _repetitions(document, "processRepetitions", 1)
