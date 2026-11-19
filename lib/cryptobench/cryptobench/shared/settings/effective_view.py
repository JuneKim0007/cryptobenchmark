"""Reading effective.yaml the way a run needs it: one KEY table, the typed views it gives, and what the run noticed joined back from report.yaml."""
import dataclasses, pathlib

from cryptobench.shared.results import skipped
from cryptobench.shared.errors.failures import CommandError, EnergyError
from cryptobench.shared import paths
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.settings import defaults, energy_capture


def read(effective_file):
    effective = pathlib.Path(effective_file)
    document = read_yaml(effective)
    report_file = paths.Configuration(effective.parent).report
    report = skipped.REPORT_DOC.check(read_yaml(report_file), report_file) if report_file.is_file() else {}
    return {
        "document": document,
        "warnings": report.get("warnings") or [],
        "skipped": report.get("skipped") or [],
    }


def entry_count(document):
    return sum(len(names) for types in (document.get("providers") or {}).values() for names in types.values())


def found(document, path):
    """The value at a dotted path, or None."""
    value = document
    for key in path.split("."):
        value = value.get(key) if isinstance(value, dict) else None
    return value


def required(document, path):
    """The value at a dotted path :config always writes; its absence is the coded missing_field, never a KeyError."""
    value = found(document, path)
    if value is None:
        raise CommandError(f"missing_field: {path} in effective.yaml")
    return value


def _listed(document, path):
    if not required(document, path):
        raise CommandError(f"missing_field: {path} in effective.yaml")
    return required(document, path)


def _positive(document, path):
    """RunSettings refuses below 1; a hand-edited effective.yaml is refused here the same way."""
    value = required(document, path)
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise CommandError(f"not_positive: {path} {value}")
    return value


def _whole(document, path):
    value = required(document, path)
    if not isinstance(value, int) or isinstance(value, bool):
        raise CommandError(f"invalid: {path} {value!r}, expected a whole number")
    return value


def _defaulted(document, path):
    """Analysis may chart a benchmark.json with no effective.yaml beside it: :config's default then."""
    value = found(document, path)
    return defaults.at(path) if value is None else value


# view, field, dotted path, read, honoured by a --bench run; a row with no view is read only for the host check
KEYS = (
    ("run", "metrics", "run.metrics", _listed, True),
    ("run", "process_repetitions", "run.processRepetitions", required, True),
    ("run", "resume_block_runs", "run.resumeBlockRuns", _positive, True),
    ("run", "order_seed", "run.orderSeed", _whole, False),
    # None keeps Jetpack's own sleep; RunSettings already refused a negative value
    ("run", "throttle_sleep", "run.thermalThrottleSleepSeconds", found, False),
    ("run", "case_cooldown", "run.caseCooldownSeconds", required, False),
    ("run", "launch_retries", "run.launchRetries", required, False),
    ("run", "warmup_iterations", "run.warmup.iterations", required, False),
    ("run", "warmup_jobs", "run.warmup.jobs", required, False),
    ("run", "warmup_cases", "run.warmup.cases", required, False),
    ("run", "thermal_gate", "run.thermalGate", found, False),
    ("run", "passes", "run.passes", found, False),
    (None, None, "run.harness.warmupIterations", found, False),
    (None, None, "run.harness.profiling", found, False),
    (None, None, "run.harness.cpu", found, False),
    ("gate", "kept", "run.thermalGate.temperatureKeptCelsius", required, False),
    ("gate", "cooldown_minutes", "run.thermalGate.cooldownMinutes", required, False),
    ("gate", "poll_minutes", "run.thermalGate.pollMinutes", required, False),
    ("gate", "terminate_minutes", "run.thermalGate.pollTerminateMinutes", required, False),
    ("gate", "discard_limit", "run.thermalGate.discardLimit", required, False),
    ("gate", "on_discard_limit", "run.thermalGate.onDiscardLimit", required, False),
    ("gate", "read_retries", "run.thermalGate.readRetries", required, False),
    ("gate", "read_retry_seconds", "run.thermalGate.readRetrySeconds", required, False),
    ("gate", "initial", "run.thermalGate.startMargin.initialCelsius", required, False),
    ("gate", "dynamic", "run.thermalGate.startMargin.dynamic", required, False),
    ("gate", "backoff", "run.thermalGate.startMargin.backoffFactor", required, False),
    ("gate", "maximum", "run.thermalGate.startMargin.maximumCelsius", required, False),
    ("gate", "clean_runs", "run.thermalGate.startMargin.cleanRunsToRecover", required, False),
    ("gate", "recovery", "run.thermalGate.startMargin.recoveryCelsius", required, False),
    ("analysis", "charts", "analysis.charts", _defaulted, True),
    ("analysis", "dir", "analysis.dir", found, True),
    ("analysis", "headline", "analysis.statistic.headline", _defaulted, True),
    ("analysis", "limit", "analysis.statistic.meanUpToCovPercent", _defaulted, True),
    ("analysis", "units", "analysis.units", _defaulted, True),
)
ROWS = {(view, field): (path, reading) for view, field, path, reading, _ in KEYS if view}


@dataclasses.dataclass(frozen=True)
class _View:
    """A view's attributes are its KEY rows, each read when asked, so a missing key fails where it is needed."""
    document: dict

    def __getattr__(self, field):
        row = ROWS.get((self.name, field))
        if row is None:
            raise AttributeError(f"{type(self).__name__}.{field}: no KEY row")
        path, reading = row
        return reading(self.document, path)


class RunView(_View):
    name = "run"


class GateView(_View):
    name = "gate"


class AnalysisView(_View):
    name = "analysis"


def _entries(document):
    for types in (document.get("providers") or {}).values():
        for names in types.values():
            for entry in names.values():
                yield from entry if isinstance(entry, list) else [entry]


@dataclasses.dataclass(frozen=True)
class EnergyView:
    """harness.energy of the run and of each entry: the captures the run makes and its one source."""
    document: dict

    @property
    def captures(self):
        default = energy_capture.capture(self.document.get("run"))
        return {energy_capture.capture(one, default) for one in _entries(self.document)} or {default}

    @property
    def source(self):
        """A session spans the whole run, and a run compares its cases: one source."""
        default = energy_capture.source(self.document.get("run"))
        names = {energy_capture.source(one, default) for one in _entries(self.document)} or {default}
        if len(names) > 1:
            raise EnergyError(f"energy_sources_differ: {sorted(names)}; set harness.energy.source once, for the run")
        return names.pop()


def ignored_on_host(document):
    """The dotted paths a --bench run ignores that this run sets to other than :config's default, in KEY order; a key inside one listed is not."""
    listed = []
    for _, _, path, _, host in KEYS:
        inside = any(path.startswith(f"{parent}.") for parent in listed)
        if not host and not inside and found(document, path) is not None and found(document, path) != defaults.at(path):
            listed.append(path)
    return listed
