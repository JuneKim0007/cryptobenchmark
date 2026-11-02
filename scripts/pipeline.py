#!/usr/bin/env python3
"""Runs the host pipeline in order and reports one readable failure."""
import argparse, dataclasses, json, os, pathlib, shutil, subprocess, sys, time

import bundled, clocks, effective_view, energy_stage, facts, gradle_runner, interop_stage, scope_generate, scope_results
from clocks import CLOCKS
from device import CPU_PINS, Device, DeviceError
from device_id import DeviceIdError, device_id
from energy_session import DRY_CALLS, EnergySession
from failure import fail
from scope_harness import HarnessError

ROOT = pathlib.Path(__file__).resolve().parent.parent


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


def summary(effective):
    view = effective_view.read(effective)
    for warning in view["warnings"]:
        print(f"warning: {warning}")
    for skip in view["skipped"]:
        print(f"skipped: {skip.get('provider', '*')} {skip.get('type', '*')} {skip.get('name', '*')}: {skip['reason']}")
    print(f"effective: {effective_view.entry_count(view['document'])} entries, {len(view['skipped'])} skipped")


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
        "deviceId": device_id(probe.get("runtime") or {}),
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


def measure_on_device(device, session, options, captures, metrics, into, preparation, discovery):
    data, traces = into / "benchmarkData.json", into / "traces"
    if captures - {"dry"}:
        print("measure:   CryptoBenchmark on the device" + ("" if options.stream else "; --stream shows each case"))
        before = clocks.read(device)
        device.measure(options.suppress_errors, metrics, data, preparation)
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
        gradle_runner.run("quick-bench", f"{data} {preparation / 'prepared.yaml'} {into}{joined}", options.stacktrace, options.stream, main_class="ConvertKt")


def parse_options():
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
    parser.add_argument("--harness", metavar="HARNESS_YAML",
                        help="with --device: measure perf-repair's scopes, original and patched, instead of the plan's cases")
    parser.add_argument("--interop", metavar="PLAN_YAML", help="with --bench or --device: check perf-repair's interop_plan.yaml pairs instead of measuring")
    options = parser.parse_args()
    if options.harness and not options.device:
        fail("--harness: scopes are measured only on a --device run")
    if options.device and options.discovery == "reuse":
        fail("--discovery reuse: a device run probes the device it measures")
    if options.suppress_errors and not options.device:
        fail("--suppress-errors: only a --device run reaches androidx.benchmark")
    if options.energy_accept_unresponsive and not options.device:
        fail("--energy-accept-unresponsive: only a --device run captures energy")
    return options


def discover(options, configuration, device, results):
    discovery, configured = results / "discovery", results / "configuration"
    if options.discovery == "overwrite" and discovery.exists():
        shutil.rmtree(discovery)
    discovery.mkdir(parents=True, exist_ok=True)

    print(f"config:    {configuration}")
    shipped = bundled.read(configuration)
    if shipped and not device:
        print("warning: providers.bundled: only a --device run builds and installs bundled providers; this run measures the platform's")
    if device:
        started = time.monotonic()
        device.install(bundled.gradle_properties(shipped))
        elapsed("build and install", started)
        started = time.monotonic()
        device.probe(discovery, bundled.instrumentation_arguments(shipped))
        capture, trial = newest(discovery, "probe_2*.yaml"), newest(discovery, "trial_*.yaml")
        if not capture or not trial:
            fail(f"missing_file: {discovery}/probe_<utc>.yaml, trial_<utc>.yaml (DeviceProbe wrote none)")
        known = facts.gather(device, discovery, capture)
        written = gradle_runner.run("jca-contract", f"{capture} {trial} {configured} {configuration} --facts={known}", options.stacktrace, options.stream, main_class="ConfigureKt")
    else:
        reuse = " --reuse" if options.discovery == "reuse" else ""
        started = time.monotonic()
        written = gradle_runner.run("jca-contract", f"{discovery} {configured} {configuration}{reuse}", options.stacktrace, options.stream)
    for path in written:
        print(f"wrote:     {path}")
    effective = configured / "effective.yaml"
    if not effective.is_file():
        fail(f"missing_file: {effective}")
    if device:
        bundled.check_effective(effective, shipped)
    summary(effective)
    elapsed("discover and configure", started)
    capture, trial = newest(discovery, "probe_2*.yaml"), newest(discovery, "trial_*.yaml")
    files = {key: path for key, path in (("probe", capture), ("trial", trial), ("inventory", configured / "inventory.yaml"),
                                         ("effective", effective), ("report", configured / "report.yaml")) if path and path.is_file()}
    return discovery, effective, capture, trial, files


def energy_preflight(options, session, discovery, files):
    started = time.monotonic()
    capability = energy_stage.preflight(session, discovery, options.energy_python, options.energy_accept_unresponsive,
                                        stacktrace=options.stacktrace)
    files["energyCapability"] = capability
    elapsed("energy pre-flight and settle", started)
    return capability


def push(device, options, plan):
    device.push_plan(*plan)
    if options.suppress_errors:
        print(f"warning: suppressErrors {options.suppress_errors}: these numbers are not comparable to an unsuppressed run")


def record(files, into, captures, device):
    if captures - {"none"}:
        files.setdefault("energy", []).append(into / "energy.json")
    if device and captures - {"dry"}:
        files.setdefault("clocks", []).append(into / CLOCKS)
        if (into / CPU_PINS).is_file():
            files.setdefault("cpuPins", []).append(into / CPU_PINS)
            import yaml
            for case, pin in (yaml.safe_load((into / CPU_PINS).read_text()) or {}).items():
                if "failed" in pin:
                    print(f"warning: cpu_pin_failed: {case}: {pin['failed']}")


def collapse(files, preparation, repetitions):
    files.update(prepared=preparation / "prepared.yaml", skipped=preparation / "skipped.yaml")
    for single in ("energy", "clocks", "cpuPins"):
        if single in files and repetitions == 1:
            files[single] = files[single][0]


def analyse(results, files, effective, preparation, benchmark, written, repetitions):
    print(f"wrote:     {benchmark / 'benchmark.json'}")
    files["benchmark"] = benchmark / "benchmark.json"
    if repetitions > 1:
        files["processes"] = written
    started = time.monotonic()
    subprocess.run([sys.executable, str(ROOT / "tools/quick-bench/analyze.py"), str(benchmark / "benchmark.json"), str(results / "analysis"),
                    str(effective), str(preparation / "prepared.yaml")], check=True)
    subprocess.run([sys.executable, str(ROOT / "tools/quick-bench/charts.py"), str(benchmark / "benchmark.json"),
                    str(preparation / "prepared.yaml"), str(effective), str(results)], check=True)
    elapsed("analyse", started)


def generate_scopes(options, scoped):
    if scoped.exists():
        shutil.rmtree(scoped)
    started = time.monotonic()
    plan, compiled = scope_generate.generate(options.harness, ROOT, scoped)
    elapsed(f"generate and compile {len(compiled)} scopes", started)
    print(f"wrote:     {plan}")
    if not compiled:
        fail(f"no_scope_compiled: every scope is not_compilable, see {plan}")
    return plan


@dataclasses.dataclass
class ScopedRun:
    discovery: pathlib.Path
    effective: pathlib.Path
    files: dict
    session: EnergySession
    capture: str
    ran: bool


def measure_scopes(options, configuration, device, results, scoped):
    discovery, effective, capture, trial, files = discover(options, configuration, device, results)
    document = effective_view.read(effective)["document"]
    run_capture = energy_stage.capture(document.get("run"))
    if run_capture == "dry":
        fail("not_supported: run.harness.energy.capture dry with --harness; use measured or none")
    session, plan_files = EnergySession(device), [effective, capture, trial]
    if run_capture == "measured":
        plan_files.append(energy_preflight(options, session, discovery, files))
    push(device, options, plan_files)
    print("measure:   ScopedBenchmark on the device")
    started, before = time.monotonic(), clocks.read(device)
    ran = device.measure_scoped(options.suppress_errors, effective_view.metrics(document),
                                scoped / "benchmarkData.json", scoped / "scoped-interop.yaml")
    clocks.write(scoped / CLOCKS, before, clocks.read(device))
    elapsed("interop check and measure", started)
    return ScopedRun(discovery, effective, files, session, run_capture, ran)


def convert_scopes(options, plan, scoped, run):
    files = run.files
    document, measured = scope_results.merge(plan, scoped / "scoped-interop.yaml")
    files.update(scopedPlan=plan, scopedInterop=scoped / "scoped-interop.yaml", clocks=scoped / CLOCKS)
    for record in document["scopes"]:
        print(f"scope:     {record['id']} {record['status']}" + (f": {record['reason']}" if record.get("reason") else "")
              + (f" ({record['interop'].get('reason')})" if record.get("interop", {}).get("reason") else ""))
    if not (run.ran and measured):
        return
    prepared = scope_results.prepared(document, measured, run.effective, scoped / "prepared.yaml")
    joined = ""
    if run.capture == "measured":
        print(f"traces:    {run.session.pull_traces(scoped / 'traces')} pulled")
        energy_stage.joules(options.energy_python, {"measured"}, run.discovery / "energy.yaml", scoped, scoped / "benchmarkData.json",
                            scoped / "traces", None, scoped / "energy.json", stacktrace=options.stacktrace)
        files["energy"], joined = scoped / "energy.json", f" {scoped / 'energy.json'}"
    gradle_runner.run("quick-bench", f"{scoped / 'benchmarkData.json'} {prepared} {scoped}{joined}", options.stacktrace, options.stream, main_class="ConvertKt")
    files["scoped"] = scoped / "benchmark.json"
    print(f"wrote:     {files['scoped']}")
    if (scoped / CPU_PINS).is_file():
        files["cpuPins"] = scoped / CPU_PINS


def harness_run(options, configuration, device, results):
    scoped = results / "scoped"
    try:
        plan = generate_scopes(options, scoped)
        run = measure_scopes(options, configuration, device, results, scoped)
    except (HarnessError, scope_generate.GenerateError) as error:
        fail(str(error))
    finally:
        scope_generate.clean(ROOT)
    convert_scopes(options, plan, scoped, run)
    manifest(results, "device", configuration, run.files)


def interop_run(options, configuration, device, results):
    plan = pathlib.Path(options.interop)
    if not (options.bench or device) or options.harness:
        fail("--interop: the pairs are checked on a --bench (host JVM) or a --device run, without --harness")
    if not plan.is_file():
        fail(f"missing_file: {plan} (--interop)")
    discovery, effective, capture, trial, files = discover(options, configuration, device, results)
    staged = interop_stage.stage_plan(plan, results / "interop")
    out = staged.parent / interop_stage.RESULT
    started = time.monotonic()
    if device:
        interop_stage.on_device(device, effective, capture, trial, staged, out)
    else:
        interop_stage.on_host(capture, trial, staged, out, options.stacktrace, options.stream)
    elapsed("interop check", started)
    interop_stage.summary(out)
    print(f"wrote:     {out}")
    files.update(interopPlan=staged, interop=out)
    manifest(results, "device" if device else "host", configuration, files)


def main():
    options = parse_options()
    sys.stdout.reconfigure(line_buffering=True)
    configuration = global_config(options.config)
    device = Device(ROOT, options.stream, options.stacktrace) if options.device else None
    if device:
        device.connect()
    results = pathlib.Path(options.results).resolve()
    if options.interop:
        return interop_run(options, configuration, device, results)
    if options.harness:
        harness_run(options, configuration, device, results)
        return
    discovery, effective, capture, trial, files = discover(options, configuration, device, results)
    mode = "device" if device else "host"
    if not (options.bench or device):
        manifest(results, mode, configuration, files)
        return

    benchmark, preparation = results / "benchmark", results / "preparation"
    started = time.monotonic()
    document = effective_view.read(effective)["document"]
    repetitions, metrics = effective_view.process_repetitions(document), effective_view.metrics(document)
    captures = energy_stage.captures(effective)
    energy = captures - {"none"}
    timed = bool(captures - {"dry"})
    if energy and not device:
        fail("energy: only a --device run captures energy; set harness.energy.capture none for --bench")
    plan = [effective, capture, trial]
    session = EnergySession(device) if device else None
    if energy:
        plan.append(energy_preflight(options, session, discovery, files))
    if device:
        push(device, options, plan)
    written = []
    for repetition in range(1, repetitions + 1):
        into = benchmark if repetitions == 1 else benchmark / f"process-{repetition}"
        if repetitions > 1:
            print(f"process:   {repetition} of {repetitions}")
        if device:
            measure_on_device(device, session, options, captures, metrics, into, preparation, discovery)
        else:
            gradle_runner.run("quick-bench", f"{capture} {trial} {effective} {into} {preparation}", options.stacktrace, options.stream)
        if timed:
            written.append(into / "benchmark.json")
        record(files, into, captures, device)
    if repetitions > 1 and timed:
        gradle_runner.run("quick-bench", " ".join([str(benchmark)] + [str(path) for path in written]), options.stacktrace, options.stream, main_class="MergeRunsKt")
    print(f"wrote:     {preparation / 'prepared.yaml'}")
    elapsed("prepare and measure", started)
    collapse(files, preparation, repetitions)
    if timed:
        analyse(results, files, effective, preparation, benchmark, written, repetitions)
    manifest(results, mode, configuration, files)

if __name__ == "__main__":
    try:
        main()
    except (DeviceError, DeviceIdError, energy_stage.EnergyError, bundled.BundledError, scope_results.ScopeResultError) as error:
        fail(str(error))
