#!/usr/bin/env python3
"""Runs the host pipeline in order and reports one readable failure."""
import argparse, json, os, pathlib, subprocess, sys, traceback

import dependencies  # first: it reports a missing PyYAML, which the imports below need
import bundled, energy_stage, timeouts
from device.adb import Device, DeviceError
from device.identity import DeviceIdError, device_id
from failure import fail, one_line
from global_file import global_config
from repo import BENCHMARK, ROOT
from results import layout as results_layout
from results import run_inputs
from results.manifest import manifest
from scope import code_digest
from scope import results as scope_results
from stages import config_check
from stages.benchmark import measure_cases
from stages.discover import device_discover, host_runtime
from stages.harness import harness_run, measured_folder
from stages.interop import interop_run


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
                        help="with --device: measure perf-repair's scopes, original and patched, instead of the plan's cases")
    parser.add_argument("--interop", metavar="PLAN_YAML", help="with --bench or --device: check perf-repair's interop_plan.yaml pairs instead of measuring")
    options = parser.parse_args()
    for refused, message in REFUSED:
        if refused(options):
            fail(message)
    return options


REFUSED = (
    (lambda o: (o.probe or o.identify) and (o.bench or o.harness or o.interop),
     "--probe, --identify: no measuring, so neither goes with --bench, --harness or --interop"),
    (lambda o: o.harness and not o.device, "--harness: scopes are measured only on a --device run"),
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
    return pathlib.Path(options.results or ROOT / "results").expanduser().resolve()


def main():
    options = parse_options()
    sys.stdout.reconfigure(line_buffering=True)
    configuration = global_config(options.config)
    # before any build; --identify runs no stage and starts no Gradle
    if not options.identify:
        config_check.parsed(configuration)
    dependencies.check(options, configuration)
    device = Device(BENCHMARK, options.stream, options.stacktrace) if options.device else None
    if device:
        device.connect()
    if options.identify:
        return identify(options, configuration, device)
    if options.harness:
        return harness_run(options, configuration, device, measured_folder(options))
    root = results_root(options)
    results_layout.warn_if_temp(root)
    if options.interop:
        return interop_run(options, configuration, device, root)
    results, (discovery, effective, capture, trial, files) = device_discover(options, configuration, device, root)
    problems = []
    if not options.probe and (options.bench or device):
        measure_cases(options, device, results, discovery, effective, capture, trial, files, problems)
    manifest(results, "device" if device else "host", configuration, files, problems)


KNOWN = (DeviceError, DeviceIdError, energy_stage.EnergyError, bundled.BundledError, config_check.ConfigCheckError,
         scope_results.ScopeResultError, code_digest.CodeDigestError, timeouts.StepTimeout)


def failure_line(error):
    """Every error the run did not survive, as one coded line; --stacktrace adds the traceback."""
    if isinstance(error, KNOWN):
        return str(error)
    if isinstance(error, subprocess.CalledProcessError):
        return f"subprocess_failed: {' '.join(map(str, error.cmd))[:300]} exited {error.returncode}"
    return f"internal_error: {type(error).__name__}: {one_line(error)}"


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        if "--stacktrace" in sys.argv:
            traceback.print_exc()
        fail(failure_line(error))
