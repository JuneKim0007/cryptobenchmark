"""Reading effective.yaml the way a run needs it: the settings, with what the run noticed joined back from report.yaml."""
import pathlib

from cryptobench.shared.errors.failures import CommandError
from cryptobench.shared import paths
from cryptobench.shared.document.document import read_yaml


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
            raise CommandError(f"missing_field: {path} in effective.yaml")
    return value


def metrics(document):
    listed = required(document, "run.metrics")
    if not listed:
        raise CommandError("missing_field: run.metrics in effective.yaml")
    return listed


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


def resume_block_runs(document):
    """RunSettings refuses below 1; a hand-edited effective.yaml is refused here the same way."""
    runs = required(document, "run.resumeBlockRuns")
    if not isinstance(runs, int) or isinstance(runs, bool) or runs < 1:
        raise CommandError(f"not_positive: run.resumeBlockRuns {runs}")
    return runs


def order_seed(document):
    """run.orderSeed, which :config requires of every run; a hand-edited value that is not whole is refused here."""
    seed = required(document, "run.orderSeed")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise CommandError(f"invalid: run.orderSeed {seed!r}, expected a whole number")
    return seed
