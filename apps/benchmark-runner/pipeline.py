#!/usr/bin/env python3
"""Runs the host pipeline in order and reports one readable failure."""
import argparse, contextlib, json, os, pathlib, subprocess, sys, traceback

import dependencies  # first: it reports a missing PyYAML, which the imports below need
from cryptobench.shared.device import aliases, probe
from cryptobench.shared.device.adb import Device
from cryptobench.shared.device.identity import device_id
from failure import fail, reported
from cryptobench.shared.errors.line import one_line
from cryptobench.shared.errors.coded import Coded
from cryptobench.shared.log.warn import warn
from cryptobench.shared.log.stdout import IDENTITY, WROTE, say
from cryptobench.pipeline.orchestrator import plan as session_plan
from cryptobench.pipeline.orchestrator import run as session_run
from cryptobench.pipeline.stage import Stage, StageContext
from cryptobench.stages.configuration.global_file import global_config
from cryptobench.shared import paths
from cryptobench.shared.results import layout as results_layout
from cryptobench.shared.results import identity as run_identity, partial, run_inputs
from cryptobench.shared.results.lock import DeviceLock
from cryptobench.shared.results.manifest import manifest
from cryptobench.shared.stop.child import stop_like_ctrl_c
from cryptobench.stages.verification.scope import code_digest
from cryptobench.stages.analysis import not_measured
from cryptobench.stages.analysis.scripts import analyse
from cryptobench.stages.configuration import config_check, guide
from cryptobench.stages.measurement import resume
from cryptobench.stages.measurement.validation import audit
from cryptobench.stages.measurement.benchmark import measure_cases
from cryptobench.stages.verification.check import check_run, require_check_run
from cryptobench.stages.discovery.discover import discover_in_place, discover_published, discover_staged, host_runtime, keep_nothing, located
from cryptobench.stages.verification.harness import harness_run, checked_folder
from cryptobench.stages.verification.interop import interop_run


def parse_options():
    options = parser().parse_args()
    for refused, message in REFUSED:
        if refused(options):
            fail(message)
    options.discovery = options.discovery or "overwrite"
    return options


def parser():
    """Every flag; shared/results/run_record.py FLAGS classifies each one (tests/test_run_contract.py)."""
    parser = argparse.ArgumentParser(description="run the host pipeline")
    parser.add_argument("--config", help="path to global.yaml")
    parser.add_argument("--results", help="results root; the run writes <results>/<device_id>/ (default: <repo>/results)")
    parser.add_argument("--discovery", choices=results_layout.DISCOVERY_MODES,
                        help="overwrite (default): clear the discovery directory first; keep: add a new capture; reuse: keep the existing capture for this device; "
                             "verify (--device): the stored capture of this build from --probe-store, else a probe that is then stored")
    parser.add_argument("--probe-store", metavar="DIR", help="with --discovery verify: one capture+trial per build key, shared across runs")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--bench", action="store_true", help="also prepare, measure and analyse (the benchmark CLI on the JVM, then the analysis scripts)")
    mode.add_argument("--device", action="store_true", help="probe, prepare and measure on the attached device (adb, ANDROID_HOME)")
    parser.add_argument("--probe", action="store_true",
                        help="discovery and configure only, with --device on the device; writes <results>/<device_id>/ and its manifest, measures nothing")
    parser.add_argument("--devices", action="store_true",
                        help="list what adb sees: each device's key, alias, kind, model, API level and connection, or why it is not ready; reads no config")
    parser.add_argument("--session", metavar="SESSION_YAML",
                        help="run a session.yaml: each target's suites as pipeline.py workers, order groups in ascending order, a summary table")
    parser.add_argument("--audit", metavar="RESULTS",
                        help="read every measured unit under RESULTS and write RESULTS/audit.yaml: per case runs, relaunches, rejected attempts, outliers; changes nothing else")
    parser.add_argument("--check-session", metavar="SESSION_YAML",
                        help="resolve a session.yaml against the devices adb lists and print its targets, order groups and skips; runs nothing")
    parser.add_argument("--per-suite", action="store_true",
                        help="write <results>/<device_id>/<suite>/, suite the file stem of global.yaml's selection.testSet: a session's layout")
    parser.add_argument("--identify", action="store_true",
                        help="print the device id, the digests of this run's inputs and of the harness code as one 'identity:' line; runs no stage, writes nothing")
    parser.add_argument("--suppress-errors", default=os.environ.get("CRYPTOBENCH_SUPPRESS_ERRORS", ""), metavar="ERRORS",
                        help="androidx.benchmark errors to suppress on --device, e.g. EMULATOR,UNLOCKED; the numbers are then not comparable")
    parser.add_argument("--energy-python", default=sys.executable, metavar="PYTHON",
                        help="interpreter with apps/benchmark-runner/energy/requirements.txt installed (default: this one, else the energy source's venv, installed on first use under the user cache)")
    parser.add_argument("--energy-accept-unresponsive", action="store_true",
                        help="run energy cases even when the rails do not respond to load; for plumbing tests only, the joules are not measurements")
    parser.add_argument("--reconnect-wait-minutes", type=int, metavar="M",
                        help="with --device: how long a lost adb transport is waited for before the run stops (default in shared/device/reconnect.py)")
    parser.add_argument("--reconnect-poll-seconds", type=int, metavar="S",
                        help="with --device: how often adb get-state is asked while waiting (default in shared/device/reconnect.py)")
    parser.add_argument("--stacktrace", action="store_true", help="print the tool's full output on failure")
    parser.add_argument("--stream", action="store_true", help="show each tool's progress while it runs")
    parser.add_argument("--harness", metavar="HARNESS_YAML",
                        help="with --device: interop-check perf-repair's scopes, original against patched, instead of the plan's cases")
    parser.add_argument("--interop", metavar="PLAN_YAML", help="with --bench or --device: check perf-repair's interop_plan.yaml pairs instead of measuring")
    parser.add_argument("--check", action="store_true",
                        help="with --bench or --device: call every planned case once, untimed, in one process, and check its output; writes check/check.yaml")
    return parser


REFUSED = (
    (lambda o: (o.probe or o.identify) and (o.bench or o.harness or o.interop),
     "--probe, --identify: no measuring, so neither goes with --bench, --harness or --interop"),
    (lambda o: o.harness and not o.device, "--harness: scopes are checked only on a --device run"),
    (lambda o: o.check and (o.probe or o.identify or o.harness or o.interop), "--check: runs alone with --bench or --device, without --probe, --identify, --harness or --interop"),
    (lambda o: o.session and (o.discovery or o.probe_store),
     "--session: discovery and probeStore are session.yaml keys, so it goes with no --discovery or --probe-store"),
    (lambda o: o.device and o.discovery == "reuse", "--discovery reuse: a device run probes the device it measures"),
    (lambda o: o.discovery == "verify" and not (o.device and o.probe_store),
     "--discovery verify: a --device run with --probe-store DIR checks the stored probe of this build"),
    (lambda o: o.probe_store and o.discovery != "verify", "--probe-store: read only by --discovery verify"),
    (lambda o: o.suppress_errors and not (o.device or o.session), "--suppress-errors: only a --device run reaches androidx.benchmark"),
    (lambda o: o.energy_accept_unresponsive and not o.device,
     "--energy-accept-unresponsive: only a --device run captures energy"),
    (lambda o: (o.reconnect_wait_minutes is not None or o.reconnect_poll_seconds is not None) and not o.device,
     "--reconnect-wait-minutes, --reconnect-poll-seconds: only a --device run waits for its device"),
    (lambda o: any(v is not None and v < 0 for v in (o.reconnect_wait_minutes, o.reconnect_poll_seconds)),
     "--reconnect-wait-minutes, --reconnect-poll-seconds: negative"),
    (lambda o: o.per_suite and (o.identify or o.harness), "--per-suite: places a run's folder, so it goes with no --identify or --harness"),
    (lambda o: o.devices and any((o.config, o.bench, o.device, o.probe, o.identify, o.check, o.harness, o.interop)),
     "--devices: lists the attached devices and runs alone"),
    (lambda o: o.audit and any((o.check_session, o.session, o.devices, o.config, o.bench, o.device, o.probe, o.identify, o.check, o.harness, o.interop,
                                o.per_suite)),
     "--audit: reads a campaign's results and runs alone"),
    (lambda o: o.check_session and any((o.devices, o.config, o.bench, o.device, o.probe, o.identify, o.check, o.harness, o.interop)),
     "--check-session: resolves a session and runs alone"),
    (lambda o: o.session and any((o.check_session, o.devices, o.config, o.bench, o.device, o.probe, o.identify, o.check, o.harness, o.interop, o.per_suite)),
     "--session: picks each worker's mode and config itself, so it goes with no mode, --config or --per-suite"),
)


def list_devices():
    """Before any config: adb's transports classified, with the user's aliases."""
    adb = Device(paths.repo().gradle_root, False, False)
    adb.require_adb()
    rows = probe.enumerate_devices(adb.raw)
    for line in probe.listing(rows, aliases.read(paths.user_devices())):
        print(line)
    if not rows:
        warn("no_device: adb lists no device; attach one or start an emulator")


def worker_options(options):
    """What a session passes on to every worker; device-only options reach device workers through their environment."""
    return (["--stacktrace"] if options.stacktrace else []) + (["--energy-python", options.energy_python] if options.energy_python != sys.executable else [])


def identify(options, configuration, device):
    """The device id before any probe: getprop on a device, the JVM's fields on a host; the probe's capture gives the same."""
    runtime = device.identity() if device else host_runtime(options)
    identity = {"deviceId": device_id(runtime), "mode": "device" if device else "host", "config": str(configuration),
                "inputs": run_inputs.digests(configuration), "harness": code_digest.digest(), "code": run_identity.code()}
    say(IDENTITY, json.dumps(identity, sort_keys=True))


def results_root(options):
    return pathlib.Path(options.results or paths.repo().default_results).expanduser().resolve()


@contextlib.contextmanager
def published(context):
    """The results root, after its temporary-folder warning, held by this run alone: a second run on it is device_busy."""
    root = results_root(context.options)
    results_layout.warn_if_temp(root)
    with DeviceLock.take(root):
        yield root


def identified(context):
    return identify(context.options, context.configuration, context.device)


def harnessed(context):
    return harness_run(context.options, context.configuration, context.device, checked_folder(context.options), context.checked["bundled"],
                       discover_in_place, reported)


def interoperated(context):
    with published(context) as root:
        return interop_run(context.options, context.configuration, context.device, root, context.checked["bundled"], discover_staged, located,
                           context.suite)


def guided(context, root, kept):
    """Discovery published under the capture's device id, the earlier unit's kept paths left in place, then guide.yaml beside its effective.yaml."""
    results, found = discover_published(context.options, context.configuration, context.device, root, context.checked["bundled"], kept, context.suite)
    found.files["guide"] = guide.write(found.effective, found.capture)
    return results, found


def guided_in(context):
    """guided's steps inside a stage the caller publishes: discovery there, then guide.yaml beside its effective.yaml."""
    def discovered(root, stage):
        found = discover_staged(context.options, context.configuration, context.device, root, stage, context.checked["bundled"], context.suite)
        found.files["guide"] = guide.write(found.effective, found.capture)
        return found
    return discovered


def checked(context):
    require_check_run(context.options, context.device)
    with published(context) as root:
        return check_run(context.options, context.configuration, context.device, root, guided_in(context), located, context.suite)


def measured(context):
    options, configuration, device = context.options, context.configuration, context.device
    measuring = not options.probe and bool(options.bench or device)
    with published(context) as root:
        # only a measuring run resumes: a probe over a stopped run moves it aside whole
        plans = []
        kept = (lambda effective, capture, target: plans.append(resume.planned(effective, capture, target, options)) or plans[-1].kept) \
            if measuring else keep_nothing
        results, found = guided(context, root, kept)
        redo = plans[-1] if plans else resume.NOTHING
        files = found.files
        mode, resumed = "device" if device else "host", resume.note(results) if measuring else []
        run = resume.record(found.effective, found.capture, options)
        if measuring:
            stopped = lambda record, pulled: manifest(results, mode, configuration, files | pulled, context.problems, partial=record, resumed=resumed, run=run)
            with partial.kept(results, stopped):
                benchmarked(options, device, results, found, context.problems, run, redo)
        manifest(results, mode, configuration, files, context.problems, resumed=resumed, run=run)
        results_layout.report_superseded(results)


def benchmarked(options, device, results, found, problems, run, redo):
    """Measurement, then the analysis of what it timed; redo: the restart's resume.RedoPlan."""
    timed, written, repetitions = measure_cases(options, device, results, found, problems, dependencies.require_energy, run, redo)
    if timed:
        benchmark, preparation = paths.RunTree(results).benchmark.root, paths.RunTree(results).preparation.root
        not_measured.report(paths.Preparation(preparation).prepared, paths.Measurement(benchmark).json, problems)
        analyse(results, found.files, found.effective, preparation, benchmark, written, repetitions)


# the first row whose option is set runs; None marks the plain run, the last row; holds_device: a --device run takes the phone's lock
ROUTES: tuple[tuple[str | None, Stage, bool], ...] = (
    ("identify", identified, False), ("harness", harnessed, True), ("interop", interoperated, True), ("check", checked, True),
    (None, measured, True))


@contextlib.contextmanager
def phone_held(device):
    """One run per phone, whatever its results root; a blank serial names no phone, so that run is not locked."""
    serial = device.serial()
    if not serial:
        warn("unstable_id: adb reports no serial for this device; a second run on it is not refused")
        yield
        return
    with DeviceLock.take_key(paths.phone_lock(serial), f"phone {serial}"):
        yield


def main():
    stop_like_ctrl_c()
    options = parse_options()
    sys.stdout.reconfigure(line_buffering=True)
    if options.devices:
        return list_devices()
    if options.session:
        # device workers inherit it, host workers never get it (worker.environment)
        os.environ["CRYPTOBENCH_SUPPRESS_ERRORS"] = options.suppress_errors
        return session_run.run_session(pathlib.Path(options.session), results_root(options), lambda: global_config(None), worker_options(options))
    if options.check_session:
        return session_plan.check(options.check_session, results_root(options), lambda: global_config(None))
    if options.audit:
        return say(WROTE, audit.written(pathlib.Path(options.audit).expanduser().resolve()))
    configuration = global_config(options.config)
    # before any build; --identify runs no stage and starts no Gradle
    checked = None if options.identify else config_check.parsed(configuration)
    dependencies.check(options, configuration)
    device = Device(paths.repo().gradle_root, options.stream, options.stacktrace) if options.device else None
    if device:
        device.connect()
    stage, holds_device = next((stage, holds) for option, stage, holds in ROUTES if option is None or getattr(options, option))
    suite = pathlib.Path(checked["testSet"]).stem if options.per_suite and checked else None
    with phone_held(device) if device and holds_device else contextlib.nullcontext():
        return stage(StageContext(options, configuration, device, checked, suite))


def failure_line(error):
    """Every error the run did not survive, as one coded line; --stacktrace adds the traceback."""
    if isinstance(error, Coded):
        return str(error)
    if isinstance(error, subprocess.CalledProcessError):
        return f"subprocess_failed: {' '.join(map(str, error.cmd))[:300]} exited {error.returncode}"
    return f"internal_error: {type(error).__name__}: {one_line(error)}"


if __name__ == "__main__":
    try:
        with reported():
            main()
    except Exception as error:
        if "--stacktrace" in sys.argv:
            traceback.print_exc()
        fail(failure_line(error))
