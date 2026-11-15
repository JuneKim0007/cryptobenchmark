#!/usr/bin/env python3
"""Runs the host pipeline in order and reports one readable failure."""
import argparse, json, os, pathlib, subprocess, sys, traceback

import dependencies  # first: it reports a missing PyYAML, which the imports below need
from cryptobench.shared.device.adb import Device
from cryptobench.shared.device.identity import device_id
from failure import fail, reported
from cryptobench.shared.errors.line import one_line
from cryptobench.shared.errors.coded import Coded
from cryptobench.pipeline.stage import Stage, StageContext
from cryptobench.stages.configuration.global_file import global_config
from cryptobench.shared import paths
from cryptobench.shared.results import layout as results_layout
from cryptobench.shared.results import run_inputs
from cryptobench.shared.results.manifest import manifest
from scope import code_digest
from cryptobench.stages.analysis import not_measured
from cryptobench.stages.analysis.scripts import analyse
from cryptobench.stages.configuration import config_check, guide
from cryptobench.stages.measurement.benchmark import measure_cases
from cryptobench.stages.verification.check import check_run, require_check_run
from cryptobench.stages.discovery.discover import discover_published, discover_staged, host_runtime, located
from stages.harness import harness_run, checked_folder
from cryptobench.stages.verification.interop import interop_run


def parse_options():
    parser = argparse.ArgumentParser(description="run the host pipeline")
    parser.add_argument("--config", help="path to global.yaml")
    parser.add_argument("--results", help="results root; the run writes <results>/<device_id>/ (default: <repo>/results)")
    parser.add_argument("--discovery", choices=["overwrite", "keep", "reuse"], default="overwrite",
                        help="overwrite: clear the discovery directory first; keep: add a new capture; reuse: keep the existing capture for this device")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--bench", action="store_true", help="also prepare, measure and analyse (the benchmark CLI on the JVM, then the analysis scripts)")
    mode.add_argument("--device", action="store_true", help="probe, prepare and measure on the attached device (adb, ANDROID_HOME)")
    parser.add_argument("--probe", action="store_true",
                        help="discovery and configure only, with --device on the device; writes <results>/<device_id>/ and its manifest, measures nothing")
    parser.add_argument("--identify", action="store_true",
                        help="print the device id, the digests of this run's inputs and of the harness code as one 'identity:' line; runs no stage, writes nothing")
    parser.add_argument("--suppress-errors", default=os.environ.get("CRYPTOBENCH_SUPPRESS_ERRORS", ""), metavar="ERRORS",
                        help="androidx.benchmark errors to suppress on --device, e.g. EMULATOR,UNLOCKED; the numbers are then not comparable")
    parser.add_argument("--energy-python", default=sys.executable, metavar="PYTHON",
                        help="interpreter with apps/benchmark-runner/energy/requirements.txt installed (default: this one)")
    parser.add_argument("--energy-accept-unresponsive", action="store_true",
                        help="run energy cases even when the rails do not respond to load; for plumbing tests only, the joules are not measurements")
    parser.add_argument("--stacktrace", action="store_true", help="print the tool's full output on failure")
    parser.add_argument("--stream", action="store_true", help="show each tool's progress while it runs")
    parser.add_argument("--harness", metavar="HARNESS_YAML",
                        help="with --device: interop-check perf-repair's scopes, original against patched, instead of the plan's cases")
    parser.add_argument("--interop", metavar="PLAN_YAML", help="with --bench or --device: check perf-repair's interop_plan.yaml pairs instead of measuring")
    parser.add_argument("--check", action="store_true",
                        help="with --bench or --device: call every planned case once, untimed, in one process, and check its output; writes check/check.yaml")
    options = parser.parse_args()
    for refused, message in REFUSED:
        if refused(options):
            fail(message)
    return options


REFUSED = (
    (lambda o: (o.probe or o.identify) and (o.bench or o.harness or o.interop),
     "--probe, --identify: no measuring, so neither goes with --bench, --harness or --interop"),
    (lambda o: o.harness and not o.device, "--harness: scopes are checked only on a --device run"),
    (lambda o: o.check and (o.probe or o.identify or o.harness or o.interop), "--check: runs alone with --bench or --device, without --probe, --identify, --harness or --interop"),
    (lambda o: o.device and o.discovery == "reuse", "--discovery reuse: a device run probes the device it measures"),
    (lambda o: o.suppress_errors and not o.device, "--suppress-errors: only a --device run reaches androidx.benchmark"),
    (lambda o: o.energy_accept_unresponsive and not o.device,
     "--energy-accept-unresponsive: only a --device run captures energy"),
)


def identify(options, configuration, device):
    """The device id before any probe: getprop on a device, the JVM's fields on a host; the probe's capture gives the same."""
    runtime = device.identity() if device else host_runtime(options)
    identity = {"deviceId": device_id(runtime), "mode": "device" if device else "host", "config": str(configuration),
                "inputs": run_inputs.digests(configuration), "harness": code_digest.digest()}
    print(f"identity:  {json.dumps(identity, sort_keys=True)}")


def results_root(options):
    return pathlib.Path(options.results or paths.repo().default_results).expanduser().resolve()


def published(context):
    """The results root, after its temporary-folder warning."""
    root = results_root(context.options)
    results_layout.warn_if_temp(root)
    return root


def identified(context):
    return identify(context.options, context.configuration, context.device)


def harnessed(context):
    return harness_run(context.options, context.configuration, context.device, checked_folder(context.options), context.checked["bundled"])


def interoperated(context):
    return interop_run(context.options, context.configuration, context.device, published(context), context.checked["bundled"], discover_staged, located)


def guided(context, root):
    """Discovery published under the capture's device id, then guide.yaml beside its effective.yaml."""
    results, (discovery, effective, capture, trial, files) = discover_published(context.options, context.configuration, context.device, root, context.checked["bundled"])
    files["guide"] = guide.write(effective, capture)
    return results, discovery, effective, capture, trial, files


def checked(context):
    root = published(context)
    require_check_run(context.options, context.device)
    results, _, effective, capture, trial, files = guided(context, root)
    return check_run(context.options, context.configuration, context.device, results, effective, capture, trial, files)


def measured(context):
    options, configuration, device = context.options, context.configuration, context.device
    results, discovery, effective, capture, trial, files = guided(context, published(context))
    if not options.probe and (options.bench or device):
        benchmarked(options, device, results, discovery, effective, capture, trial, files, context.problems)
    manifest(results, "device" if device else "host", configuration, files, context.problems)


def benchmarked(options, device, results, discovery, effective, capture, trial, files, problems):
    """Measurement, then the analysis of what it timed."""
    timed, written, repetitions = measure_cases(options, device, results, discovery, effective, capture, trial, files, problems, dependencies.require_energy)
    if timed:
        benchmark, preparation = paths.RunTree(results).benchmark.root, paths.RunTree(results).preparation.root
        not_measured.report(paths.Preparation(preparation).prepared, paths.Measurement(benchmark).json, problems)
        analyse(results, files, effective, preparation, benchmark, written, repetitions)


# the first row whose option is set runs; None marks the plain run, the last row
ROUTES: tuple[tuple[str | None, Stage], ...] = (
    ("identify", identified), ("harness", harnessed), ("interop", interoperated), ("check", checked), (None, measured))


def main():
    options = parse_options()
    sys.stdout.reconfigure(line_buffering=True)
    configuration = global_config(options.config)
    # before any build; --identify runs no stage and starts no Gradle
    checked = None if options.identify else config_check.parsed(configuration)
    dependencies.check(options, configuration)
    device = Device(paths.repo().gradle_root, options.stream, options.stacktrace) if options.device else None
    if device:
        device.connect()
    stage = next(stage for option, stage in ROUTES if option is None or getattr(options, option))
    return stage(StageContext(options, configuration, device, checked))


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
