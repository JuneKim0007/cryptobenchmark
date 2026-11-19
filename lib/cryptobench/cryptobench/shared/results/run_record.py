"""A measuring run's record: its identity, the flags that change its numbers and the checkout that ran it; every block record and the manifest's
run: hold it. RUN_KEYS and FLAGS classify every effective run key and pipeline.py flag (tests/test_run_contract.py)."""
import subprocess

from cryptobench.shared import paths
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.errors.failures import CommandError
from cryptobench.shared.results import identity
from cryptobench.shared.settings import effective_view

PROVENANCE = ("commit", "clean")
DATA, NOT_DATA = "data", "not_data"
# DATA: what a case measures or how it is launched, held by the record's run block; the second field is what an absence means, None when :config
# always writes the key, so its absence is missing_field
RUN_KEYS = {
    "inputSizes": (DATA, None), "phases": (DATA, None), "metrics": (DATA, None), "variants": (DATA, None), "processRepetitions": (DATA, None),
    "seed": (DATA, None), "orderSeed": (DATA, None), "caseCooldownSeconds": (DATA, None), "launchRetries": (DATA, None), "warmup": (DATA, None),
    "energyIdleSeconds": (DATA, None),
    "passes": (DATA, "one pass measures every metric"), "thermalThrottleSleepSeconds": (DATA, "Jetpack's own sleep"),
    "thermalGate": (DATA, "no gate"), "harness": (DATA, "the harness defaults"),
    "resumeBlockRuns": (NOT_DATA, "how a rerun keeps blocks, not what a run measures"),
}
# DATA: a flag that changes a measuring run's numbers, held by the record under the field named; NOT_DATA: why it changes none
FLAGS = {
    "suppress_errors": (DATA, "suppressErrors"),
    "energy_accept_unresponsive": (DATA, "energyAcceptUnresponsive"),
    "config": (NOT_DATA, "its effective.yaml is the record's run block and selection"),
    "discovery": (NOT_DATA, "the capture it keeps or makes is the record's device"),
    "probe_store": (NOT_DATA, "the stored capture is the record's device"),
    "bench": (NOT_DATA, "the host or device is the record's device"),
    "device": (NOT_DATA, "the host or device is the record's device"),
    "results": (NOT_DATA, "where the run is written"),
    "per_suite": (NOT_DATA, "where the run is written"),
    "probe": (NOT_DATA, "measures nothing"),
    "identify": (NOT_DATA, "measures nothing"),
    "devices": (NOT_DATA, "measures nothing"),
    "check_session": (NOT_DATA, "measures nothing"),
    "audit": (NOT_DATA, "reads results, measures nothing"),
    "check": (NOT_DATA, "calls each case once, untimed"),
    "harness": (NOT_DATA, "checks scopes, measures nothing"),
    "interop": (NOT_DATA, "checks pairs, measures nothing"),
    "session": (NOT_DATA, "each worker's run has its own record"),
    "energy_python": (NOT_DATA, "the interpreter reads the energy trace; its packages are pinned by energy/requirements.txt"),
    "reconnect_wait_minutes": (NOT_DATA, "how long a lost device is waited for, not what is measured"),
    "reconnect_poll_seconds": (NOT_DATA, "how long a lost device is waited for, not what is measured"),
    "stacktrace": (NOT_DATA, "what a failure prints"),
    "stream": (NOT_DATA, "what progress prints"),
}


def checkout(root=None):
    """commit: HEAD of the checkout; clean: no tracked or untracked change git reports. git that cannot say is missing_field."""
    root = root or paths.repo().root
    def git(*arguments):
        return subprocess.run(["git", "-C", str(root), *arguments], capture_output=True, text=True, timeout=60, check=True).stdout.strip()
    try:
        return {"commit": git("rev-parse", "HEAD"), "clean": git("status", "--porcelain") == ""}
    except (OSError, subprocess.SubprocessError) as error:
        raise CommandError(f"missing_field: commit, git cannot say for {root}: {type(error).__name__}") from error


def resolved(document, options):
    """Every DATA run key :config always writes and every DATA flag, else missing_field; a run key no row classifies is unclassified."""
    run = effective_view.required(document, "run")
    unknown = sorted(set(run) - set(RUN_KEYS))
    if unknown:
        raise CommandError(f"unclassified: run.{unknown[0]} in effective.yaml; shared/results/run_record.py RUN_KEYS names every run key")
    for key, (kind, absent) in RUN_KEYS.items():
        if kind == DATA and absent is None:
            effective_view.required(document, f"run.{key}")
    for flag, (kind, _field) in FLAGS.items():
        if kind == DATA and getattr(options, flag, None) is None:
            raise CommandError(f"missing_field: --{flag.replace('_', '-')} unresolved for the run record")


def of(effective, capture, order, options):
    """identity.of with options.suppress_errors, energyAcceptUnresponsive and the checkout; refused when a DATA value is unresolved (resolved)."""
    resolved(read_yaml(effective), options)
    return (identity.of(effective, capture, order, options.suppress_errors) | {"energyAcceptUnresponsive": bool(options.energy_accept_unresponsive)}
            | checkout())


def changed(before, after):
    """identity.changed without the checkout: commit and clean say which tree ran, the code digests what it ran."""
    return [name for name in identity.changed(before, after) if name not in PROVENANCE]
