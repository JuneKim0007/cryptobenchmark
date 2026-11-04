"""The benchmark of a plain run: on the device in passes and sessions, or on the host JVM; then the analysis."""
import subprocess, sys, time

import dependencies, effective_view, energy_stage, gradle_runner, timeouts
from energy_session import DRY_CALLS, EnergySession
from failure import fail, one_line
from repo import RUNNER
from session import case_isolation, energy_hook, passes, variant_order, warmup
from session import measure as measure_session
from stages import not_measured
from stages.measuring import (Measuring, convert, energy_preflight, gated, pass_arguments, push, record, session_arguments, singles,
                              thermal_flag, timed_hooks)
from stages.took import elapsed


def measure_on_device(run, one, captures, preparation, isolation, repetitions, folder, written):
    device, captures = run.device, one.captures(captures)
    timed = captures - {"dry"}
    hooks = timed_hooks(run, one, isolation) if timed else []
    if captures - {"none"}:
        dry = lambda into, guarded: dry_pass(run.session, into, preparation, run.problems, guarded)
        hooks.insert(0, energy_hook.EnergyCapture(run.source, run.session, captures, run.discovery, preparation, run.problems, dry, bool(timed)))

    def converted(process):
        if timed:
            joules = process.into / "energy.json"
            joined = f" {joules}" if "measured" in captures and joules.is_file() else ""
            convert(run, f"{process.data} {preparation / 'prepared.yaml'} {process.into}{joined}{one.convert_flags()}{thermal_flag(process)}")
            written.append(process.into / "benchmark.json")
        record(run.files, process.into, captures, device)

    arguments = pass_arguments(run, one)
    plan = measure_session.Plan("CryptoBenchmark", arguments, timed=bool(timed), order=variant_order.interleaved,
                                cleared=("prepared.yaml", "skipped.yaml"), stale=(preparation / "prepared.yaml", preparation / "skipped.yaml"),
                                pull_plan=lambda process: (device.pull_plan(preparation), device.pull_pins(process.into)), after_process=converted)
    measure_session.run_session(device, plan, repetitions, isolation, hooks, folder, run.problems)


def dry_pass(session, into, preparation, problems, guarded):
    """Beside a timed run its failure costs only energy; alone it is the whole measurement."""
    print("measure:   EnergyDryBenchmark inside a host trace session")
    step = lambda: session.dry_pass(RUNNER / "energy/energy.pbtx", into / "traces/dry.pftrace", into / DRY_CALLS, preparation)
    energy_stage.guarded(problems, step) if guarded else step()


def analyse(results, files, effective, preparation, benchmark, written, repetitions):
    print(f"wrote:     {benchmark / 'benchmark.json'}")
    files["benchmark"] = benchmark / "benchmark.json"
    if repetitions > 1:
        files["processes"] = written
    started = time.monotonic()
    data, prepared = str(benchmark / "benchmark.json"), str(preparation / "prepared.yaml")
    # charts only show a benchmark already paid for: a failure warns, the first ends them, and the run keeps its files
    failed = (drawing_failed("analysis/analyze.py", data, str(results / "analysis"), str(effective), prepared)
              or drawing_failed("analysis/charts.py", data, prepared, str(effective), str(results)))
    if failed:
        print(f"warning: charts_failed: {failed}")
    elapsed("analyse", started)


def drawing_failed(script, *arguments):
    """The reason this analysis script failed, else None; what it says on stderr still reaches the run's output."""
    try:
        done = timeouts.run("analysis", [sys.executable, str(RUNNER / script), *arguments], stderr=subprocess.PIPE, text=True, check=False)
    except timeouts.StepTimeout as error:
        return one_line(error)
    if done.returncode == 0:
        if done.stderr:
            print(done.stderr, end="", file=sys.stderr)
        return None
    last = done.stderr.strip().splitlines()[-1:] or [f"exit {done.returncode}"]
    return one_line(f"{script}: {last[0]}")


def measure_cases(options, device, results, discovery, effective, capture, trial, files, problems):
    benchmark, preparation = results / "benchmark", results / "preparation"
    started = time.monotonic()
    document = effective_view.read(effective)["document"]
    repetitions, captures = effective_view.process_repetitions(document), energy_stage.captures(effective)
    timed = bool(captures - {"dry"})
    if captures - {"none"} and not device:
        fail("energy: only a --device run captures energy; set harness.energy.capture none for --bench")
    if captures - {"none"}:
        # the effective config holds the captures a test set turned on, which the first check could not see
        dependencies.require_energy(energy_stage.source_name(effective), options.energy_python)
    if device:
        run = Measuring(device, EnergySession(device), energy_stage.source(effective, options.energy_python, options.stacktrace), options, discovery,
                        files, problems, effective_view.throttle_sleep(document), effective_view.case_cooldown(document))
        written, processes = device_cases(run, document, [effective, capture, trial], captures, benchmark, preparation)
    else:
        written, processes = host_cases(options, document, capture, trial, effective, benchmark, preparation, files), repetitions
    print(f"wrote:     {preparation / 'prepared.yaml'}")
    elapsed("prepare and measure", started)
    collapse(files, preparation, processes)
    if timed:
        not_measured.report(preparation / "prepared.yaml", benchmark / "benchmark.json", problems)
        analyse(results, files, effective, preparation, benchmark, written, repetitions)


def device_cases(run, document, plan_files, captures, benchmark, preparation):
    """Every pass of the run on the device; the per-process files for the manifest and how many processes ran."""
    chosen, repetitions = passes.read(document, captures), effective_view.process_repetitions(document)
    energy = any(one.captures(captures) - {"none"} for one in chosen)
    push(run.device, run.options, plan_files, (lambda: energy_preflight(run.options, run.source, run.session, run.discovery, run.files)) if energy else None)
    isolation = effective_view.isolation(document)
    # idle baseline first: after the warm-up the device is hot and the target would never be reached
    run = gated(run, document)
    warm_up(run, document, preparation)
    measure_one = lambda one, folder, written: measure_on_device(run, one, captures, preparation, isolation, repetitions, folder, written)
    return passes.run_all(chosen, repetitions, benchmark, measure_one, run.options), repetitions * len(chosen)


def warm_up(run, document, preparation):
    """Before the first pass: the device lists its plan once, and the warm-up picks from it."""
    import yaml
    if warmup.off(document):
        return
    arguments = session_arguments(run, document)
    planned = case_isolation.listed(run.device.instrument("CryptoBenchmark", *arguments, "-e", "log", "true"))
    run.device.pull_plan(preparation)
    cases = (yaml.safe_load((preparation / "prepared.yaml").read_text()) or {}).get("cases") or []
    warmup.run(run.device, "CryptoBenchmark", arguments, planned, cases, document)


def host_cases(options, document, capture, trial, effective, benchmark, preparation, files):
    repetitions, written = effective_view.process_repetitions(document), []
    if (document.get("run") or {}).get("passes"):
        print("warning: run.passes: only a --device run measures in passes; this run measures once per process")
    if effective_view.thermal_gate(document):
        print("warning: thermal_gate_off: run.thermalGate: only a --device run reads temperatures; this run measures without the gate")
    for repetition in range(1, repetitions + 1):
        into = measure_session.process_folder(benchmark, repetition, repetitions)
        measure_session.process_line(repetition, repetitions)
        gradle_runner.run(f"{capture} {trial} {effective} {into} {preparation}", options.stacktrace, options.stream, main_class="BenchKt")
        written.append(into / "benchmark.json")
        record(files, into, {"none"}, None)
    if repetitions > 1:
        passes.merge_runs(benchmark, written, options)
    return written


def collapse(files, preparation, repetitions):
    files.update(prepared=preparation / "prepared.yaml", skipped=preparation / "skipped.yaml")
    singles(files, repetitions)
