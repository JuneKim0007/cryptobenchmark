"""Reading effective.yaml the way a run needs it: the settings, with what the run noticed joined back from report.yaml."""
import pathlib

import yaml

from failure import fail
from cryptobench import paths
from cryptobench.document import read_yaml

CASE_ISOLATION = "case"


def read(effective_file):
    effective = pathlib.Path(effective_file)
    document = read_yaml(effective)
    report_file = paths.Configuration(effective.parent).report
    report = (read_yaml(report_file)) if report_file.is_file() else {}
    return {
        "document": document,
        "warnings": report.get("warnings") or [],
        "skipped": report.get("skipped") or [],
    }


def entry_count(document):
    return sum(len(names) for types in (document.get("providers") or {}).values() for names in types.values())


def required(document, path):
    """The value at a dotted path :config always writes; its absence is the coded missing_field, never a KeyError."""
    value = document
    for key in path.split("."):
        value = value.get(key) if isinstance(value, dict) else None
        if value is None:
            fail(f"missing_field: {path} in effective.yaml")
    return value


def metrics(document):
    listed = required(document, "run.metrics")
    if not listed:
        fail("missing_field: run.metrics in effective.yaml")
    return listed


def isolation(document):
    return required(document, "run.isolation")


def throttle_sleep(document):
    """None keeps Jetpack's own sleep; RunSettings already refused a negative value."""
    return (document.get("run") or {}).get("thermalThrottleSleepSeconds")


def case_cooldown(document):
    return required(document, "run.caseCooldownSeconds")


def thermal_gate(document):
    """run.thermalGate as :config validated it, or None when absent."""
    return (document.get("run") or {}).get("thermalGate")


def launch_retries(document):
    return required(document, "run.launchRetries")


def process_repetitions(document):
    return required(document, "run.processRepetitions")
