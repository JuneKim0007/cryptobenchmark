#!/usr/bin/env python3
"""Runs the host pipeline in order and reports one readable failure."""
import argparse, json, os, pathlib, shutil, subprocess, sys, time

import clocks, energy_stage
from clocks import CLOCKS
from device import Device, DeviceError
from energy_session import DRY_CALLS, EnergySession

ROOT = pathlib.Path(__file__).resolve().parent.parent


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def global_config(argument):
    if argument:
        if not pathlib.Path(argument).is_file():
            fail(f"missing_file: {argument} (--config)")
        return pathlib.Path(argument).resolve()
    for candidate in (os.environ.get("CRYPTOBENCH_CONFIG"),
                      pathlib.Path.home() / ".config/cryptobench/global.yaml", ROOT / "config/global.yaml"):
        if candidate and pathlib.Path(candidate).is_file():
            return pathlib.Path(candidate).resolve()
    fail("no global.yaml: pass --config, set CRYPTOBENCH_CONFIG, or keep config/global.yaml")


def elapsed(label, started):
    print(f"took:      {label} in {time.monotonic() - started:.1f}s")


def gradle(project, arguments, stacktrace, stream=False, main_class=None):
    wrapper = ROOT / "tools/jca-contract/gradlew"
    if not wrapper.is_file():
        fail(f"missing_file: {wrapper}")
    command = [str(wrapper), "-p", str(ROOT / "tools" / project), "run", "--no-daemon", "-q", f"--args={arguments}"]
    if main_class:
        command.append(f"-PmainClass={main_class}")
    if stream:
        result = subprocess.run(command, stdout=subprocess.PIPE, text=True)
        if result.returncode != 0:
            fail(f"{project} failed; rerun without --stream for a filtered message")
        return result.stdout.strip().splitlines()
    result = subprocess.run(command, capture_output=True, text=True)
    output = (result.stdout + result.stderr).splitlines()
    if result.returncode != 0:
        if stacktrace:
            print("\n".join(output), file=sys.stderr)
        reported, following = [], False
        for line in output:
            if line.startswith(("error:", "skipped:", "warning:")):
                reported.append(line[len("error: "):] if line.startswith("error: ") else line)
                following = True
            elif following and line.startswith("  "):
                reported.append(line)
            else:
                following = False
        noise = ("FAILURE:", "BUILD FAILED", "* Try:", "* Get more help", "* What went wrong", "> Process 'command", "Run with --", "* Exception is:")
        fallback = [line for line in output if line.strip() and not line.startswith(noise)]
        fail("\n".join(reported or fallback[-5:])[:2000])
    for line in output:
        if line.startswith(("warning:", "skipped:", "reused:", "iterations_not_applied:", "allocation_runs_changed:", "no_case_in_the_plan:", "energy_not_joined:")):
            print(line)
    return result.stdout.strip().splitlines()


def process_repetitions(effective):
    import yaml
    run = yaml.safe_load(effective.read_text()).get("run") or {}
    repetitions = run.get("processRepetitions", 1)
    if not isinstance(repetitions, int) or repetitions < 1:
        fail(f"not_positive: processRepetitions {repetitions}")
    return repetitions


def summary(effective):
    import yaml
    document = yaml.safe_load(effective.read_text())
    entries = sum(len(names) for types in document["providers"].values() for names in types.values())
    for warning in document.get("warnings") or []:
        print(f"warning: {warning}")
    for skip in document.get("skipped") or []:
        print(f"skipped: {skip.get('provider', '*')} {skip.get('type', '*')} {skip.get('name', '*')}: {skip['reason']}")
    print(f"effective: {entries} entries, {len(document.get('skipped') or [])} skipped")


def newest(directory, pattern):
    return max(directory.glob(pattern), key=lambda p: p.name, default=None)


def runtime(measured, probe, files):
    document = dict(measured["runtime"] if measured else probe.get("runtime") or {})
    if "clocks" in files:
        paths = files["clocks"] if isinstance(files["clocks"], list) else [files["clocks"]]
        document["cpuLocked"] = clocks.runtime_locked(paths)
    return document


def manifest(results, mode, configuration, files):
    import yaml
    def load(key):
        text = files[key].read_text()
        return json.loads(text) if files[key].suffix == ".json" else yaml.safe_load(text)
    probe = load("probe") if "probe" in files else {}
    measured = load("benchmark") if "benchmark" in files else None
    counted = {"prepared": ("prepared", "cases"), "skipped": ("skipped", "skipped"), "measured": ("benchmark", "cases")}
    document = {
        "schemaVersion": 1,
        "mode": mode,
        "config": str(configuration),
        "runtime": runtime(measured, probe, files),
        "providers": [{"name": p["name"], "precedence": p["precedence"], "serviceCount": len(p.get("services") or [])}
                      for p in sorted(probe.get("providers") or [], key=lambda p: p["precedence"])],
        "files": {key: [path.relative_to(results).as_posix() for path in value] if isinstance(value, list)
                  else value.relative_to(results).as_posix() for key, value in files.items()},
        "counts": {count: len((measured if key == "benchmark" else load(key)).get(field) or [])
                   for count, (key, field) in counted.items() if key in files},
    }
    path = results / "manifest.yaml"
    path.write_text(yaml.safe_dump(document, sort_keys=False))
    print(f"wrote:     {path}")


def measure_on_device(device, session, options, captures, into, preparation, discovery):
    data, traces = into / "benchmarkData.json", into / "traces"
    if captures - {"dry"}:
        print("measure:   CryptoBenchmark on the device" + ("" if options.stream else "; --stream shows each case"))
        before = clocks.read(device)
        device.measure(options.suppress_errors, data, preparation)
        clocks.write(into / CLOCKS, before, clocks.read(device))
        if "measured" in captures:
            print(f"traces:    {session.pull_traces(traces)} pulled")
    if "dry" in captures:
        print("measure:   EnergyDryBenchmark inside a host trace session")
        session.dry_pass(ROOT / "tools/energy/energy.pbtx", traces / "dry.pftrace", into / DRY_CALLS, preparation)
    if captures - {"none"}:
        energy_stage.joules(options.energy_python, captures, discovery / "energy.yaml", preparation, data, traces,
                            into / DRY_CALLS, into / "energy.json", stacktrace=options.stacktrace)
    if captures - {"dry"}:
        joined = f" {into / 'energy.json'}" if "measured" in captures else ""
        gradle("quick-bench", f"{data} {preparation / 'prepared.yaml'} {into}{joined}", options.stacktrace, options.stream, main_class="ConvertKt")


def main():
    parser = argparse.ArgumentParser(description="run the host pipeline")
    parser.add_argument("--config", help="path to global.yaml")
    parser.add_argument("--results", default=str(ROOT / "results"), help="output root (default: results/)")
    parser.add_argument("--discovery", choices=["overwrite", "keep", "reuse"], default="overwrite",
                        help="overwrite: clear the discovery directory first; keep: add a new capture; reuse: keep the existing capture for this device")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--bench", action="store_true", help="also prepare, measure and analyse (quick-bench, JVM)")
    mode.add_argument("--device", action="store_true", help="probe, prepare and measure on the attached device (adb, ANDROID_HOME)")
    parser.add_argument("--suppress-errors", default="", metavar="ERRORS",
                        help="androidx.benchmark errors to suppress on --device, e.g. EMULATOR,UNLOCKED; the numbers are then not comparable")
    parser.add_argument("--energy-python", default=sys.executable, metavar="PYTHON",
                        help="interpreter with tools/energy/requirements.txt installed (default: this one)")
    parser.add_argument("--energy-accept-unresponsive", action="store_true",
                        help="run energy cases even when the rails do not respond to load; for plumbing tests only, the joules are not measurements")
    parser.add_argument("--stacktrace", action="store_true", help="print the tool's full output on failure")
    parser.add_argument("--stream", action="store_true", help="show each tool's progress while it runs")
    options = parser.parse_args()
    sys.stdout.reconfigure(line_buffering=True)

    if options.device and options.discovery == "reuse":
        fail("--discovery reuse: a device run probes the device it measures")
    if options.suppress_errors and not options.device:
        fail("--suppress-errors: only a --device run reaches androidx.benchmark")
    if options.energy_accept_unresponsive and not options.device:
        fail("--energy-accept-unresponsive: only a --device run captures energy")

    configuration = global_config(options.config)
    device = Device(ROOT, options.stream, options.stacktrace) if options.device else None
    if device:
        device.connect()
    results = pathlib.Path(options.results).resolve()
    discovery, configured = results / "discovery", results / "configuration"
    if options.discovery == "overwrite" and discovery.exists():
        shutil.rmtree(discovery)
    discovery.mkdir(parents=True, exist_ok=True)

    print(f"config:    {configuration}")
    if device:
        started = time.monotonic()
        device.install()
        elapsed("build and install", started)
        started = time.monotonic()
        device.probe(discovery)
        capture, trial = newest(discovery, "probe_2*.yaml"), newest(discovery, "trial_*.yaml")
        if not capture or not trial:
            fail(f"missing_file: {discovery}/probe_<utc>.yaml, trial_<utc>.yaml (DeviceProbe wrote none)")
        written = gradle("jca-contract", f"{capture} {trial} {configured} {configuration}", options.stacktrace, options.stream, main_class="ConfigureKt")
    else:
        reuse = " --reuse" if options.discovery == "reuse" else ""
        started = time.monotonic()
        written = gradle("jca-contract", f"{discovery} {configured} {configuration}{reuse}", options.stacktrace, options.stream)
    for path in written:
        print(f"wrote:     {path}")
    effective = configured / "effective.yaml"
    if not effective.is_file():
        fail(f"missing_file: {effective}")
    summary(effective)
    elapsed("discover and configure", started)
    capture, trial = newest(discovery, "probe_2*.yaml"), newest(discovery, "trial_*.yaml")
    files = {key: path for key, path in (("probe", capture), ("trial", trial), ("inventory", configured / "inventory.yaml"),
                                         ("effective", effective)) if path and path.is_file()}

    mode = "device" if device else "host"
    if not (options.bench or device):
        manifest(results, mode, configuration, files)
        return
    benchmark, preparation = results / "benchmark", results / "preparation"
    started = time.monotonic()
    repetitions = process_repetitions(effective)
    written = []
    captures = energy_stage.captures(effective)
    energy = captures - {"none"}
    timed = bool(captures - {"dry"})
    if energy and not device:
        fail("energy: only a --device run captures energy; set harness.energy.capture none for --bench")
    plan = [effective, capture, trial]
    session = EnergySession(device) if device else None
    if energy:
        started = time.monotonic()
        capability = energy_stage.preflight(session, discovery, options.energy_python, options.energy_accept_unresponsive,
                                            stacktrace=options.stacktrace)
        plan.append(capability)
        files["energyCapability"] = capability
        elapsed("energy pre-flight and settle", started)
    if device:
        device.push_plan(*plan)
        if options.suppress_errors:
            print(f"warning: suppressErrors {options.suppress_errors}: these numbers are not comparable to an unsuppressed run")
    for repetition in range(1, repetitions + 1):
        into = benchmark if repetitions == 1 else benchmark / f"process-{repetition}"
        if repetitions > 1:
            print(f"process:   {repetition} of {repetitions}")
        if device:
            measure_on_device(device, session, options, captures, into, preparation, discovery)
        else:
            gradle("quick-bench", f"{capture} {trial} {effective} {into} {preparation}", options.stacktrace, options.stream)
        if timed:
            written.append(into / "benchmark.json")
        if energy:
            files.setdefault("energy", []).append(into / "energy.json")
        if device and timed:
            files.setdefault("clocks", []).append(into / CLOCKS)
    if repetitions > 1 and timed:
        gradle("quick-bench", " ".join([str(benchmark)] + [str(path) for path in written]), options.stacktrace, options.stream, main_class="MergeRunsKt")
    print(f"wrote:     {preparation / 'prepared.yaml'}")
    elapsed("prepare and measure", started)
    files.update(prepared=preparation / "prepared.yaml", skipped=preparation / "skipped.yaml")
    for single in ("energy", "clocks"):
        if single in files and repetitions == 1:
            files[single] = files[single][0]
    if not timed:
        manifest(results, mode, configuration, files)
        return
    print(f"wrote:     {benchmark / 'benchmark.json'}")
    files["benchmark"] = benchmark / "benchmark.json"
    if repetitions > 1:
        files["processes"] = written
    analysis = results / "analysis"
    started = time.monotonic()
    subprocess.run([sys.executable, str(ROOT / "tools/quick-bench/analyze.py"), str(benchmark / "benchmark.json"), str(analysis)], check=True)
    elapsed("analyse", started)
    manifest(results, mode, configuration, files)


if __name__ == "__main__":
    try:
        main()
    except (DeviceError, energy_stage.EnergyError) as error:
        fail(str(error))
