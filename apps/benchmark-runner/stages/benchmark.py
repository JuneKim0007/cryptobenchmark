"""The benchmark of a plain run: on the device in passes and sessions, or on the host JVM; then the analysis."""
import subprocess, sys, time

import bundled, dependencies, effective_view, energy_stage, gradle_runner, timeouts
from energy_session import EnergySession
from failure import fail, one_line, warn
from cryptobench import paths
from session import case_isolation, energy_hook, passes, variant_order, warmup
from session import measure as measure_session
from stages import guide, not_measured
from stages.measuring import (Measuring, convert, energy_preflight, gated, pass_arguments, push, record, session_arguments, singles,
                              thermal_flag, timed_hooks)
from stages.took import elapsed
from cryptobench.document import read_yaml


def measure_on_device(run, one, captures, preparation, isolation, repetitions, folder, written):
    device, captures = run.device, one.captures(captures)
    timed = captures - {"dry"}
    gate = run.gate.session(one.label)
    hooks = timed_hooks(run, one, isolation, gate) if timed else []
    if captures - {"none"}:
        dry = lambda into, guarded: (gate.hold("energy dry pass"), dry_pass(run.session, into, preparation, run.problems, guarded))[1]
        hooks.insert(0, energy_hook.EnergyCapture(run.source, run.session, captures, run.discovery, preparation, run.problems, dry, bool(timed)))

    def converted(process):
        if timed:
            joules = paths.Measurement(process.into).energy
            joined = f" {joules}" if "measured" in captures and joules.is_file() else ""
            convert(run, f"{process.data} {paths.Preparation(preparation).prepared} {process.into}{joined}{one.convert_flags()}{thermal_flag(process)}")
            written.append(paths.Measurement(process.into).json)
        record(run.files, process.into, captures, device)

    arguments = pass_arguments(run, one)
    plan = measure_session.Plan("CryptoBenchmark", arguments, timed=bool(timed), order=variant_order.interleaved,
                                cleared=(paths.PREPARED, paths.SKIPPED), stale=(paths.Preparation(preparation).prepared, paths.Preparation(preparation).skipped),
                                pull_plan=lambda process: (device.pull_plan(preparation), device.pull_pins(process.into)), after_process=converted,
                                gate=gate, retries=run.retries)
    measure_session.run_session(device, plan, repetitions, isolation, hooks, folder, run.problems)


def dry_pass(session, into, preparation, problems, guarded):
    """Beside a timed run its failure costs only energy; alone it is the whole measurement."""
    print("measure:   EnergyDryBenchmark inside a host trace session")
    step = lambda: session.dry_pass(paths.repo().energy / "energy.pbtx", paths.Measurement(into).dry_trace, paths.Measurement(into).energy_dry, preparation)
    energy_stage.guarded(problems, step) if guarded else step()


def analyse(results, files, effective, preparation, benchmark, written, repetitions):
    print(f"wrote:     {paths.Measurement(benchmark).json}")
    files["benchmark"] = paths.Measurement(benchmark).json
    if repetitions > 1:
        files["processes"] = written
    started = time.monotonic()
    data, prepared = str(paths.Measurement(benchmark).json), str(paths.Preparation(preparation).prepared)
    # charts only show a benchmark already paid for: a failure warns, the first ends them, and the run keeps its files
    analysis = str(paths.RunTree(results).analysis.root)
    failed = (drawing_failed("analysis/analyze.py", data, analysis, str(effective), prepared)
              or drawing_failed("analysis/run_counts.py", analysis, *map(str, written if repetitions > 1 else [data]))
              or drawing_failed("analysis/charts.py", data, prepared, str(effective), str(results)))
    if failed:
        print(f"warning: charts_failed: {failed}")
    elapsed("analyse", started)


def drawing_failed(script, *arguments):
    """The reason this analysis script failed, else None; what it says on stderr still reaches the run's output."""
    try:
        done = timeouts.run("analysis", [sys.executable, str(paths.repo().runner / script), *arguments], stderr=subprocess.PIPE, text=True, check=False)
    except timeouts.StepTimeout as error:
        return one_line(error)
    if done.returncode == 0:
        if done.stderr:
            print(done.stderr, end="", file=sys.stderr)
        return None
    last = done.stderr.strip().splitlines()[-1:] or [f"exit {done.returncode}"]
    return one_line(f"{script}: {last[0]}")


def measure_cases(options, device, results, discovery, effective, capture, trial, files, problems):
    benchmark, preparation = paths.RunTree(results).benchmark.root, paths.RunTree(results).preparation.root
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
        written, processes = device_cases(run, document, [effective, guide.file_beside(effective), capture, trial], captures, benchmark, preparation)
    else:
        written, processes = host_cases(options, document, capture, trial, effective, benchmark, preparation, files, problems), repetitions
    print(f"wrote:     {paths.Preparation(preparation).prepared}")
    elapsed("prepare and measure", started)
    collapse(files, preparation, processes)
    if timed:
        not_measured.report(paths.Preparation(preparation).prepared, paths.Measurement(benchmark).json, problems)
        analyse(results, files, effective, preparation, benchmark, written, repetitions)


def device_cases(run, document, plan_files, captures, benchmark, preparation):
    """Every pass of the run on the device; the per-process files for the manifest and how many processes ran."""
    chosen, repetitions = passes.read(document, captures), effective_view.process_repetitions(document)
    energy = any(one.captures(captures) - {"none"} for one in chosen)
    run = gated(run, document)
    push(run.device, run.options, plan_files, (lambda: energy_preflight(run.options, run.source, run.session, run.discovery, run.files)) if energy else None)
    isolation = effective_view.isolation(document)
    warm_up(run, document, preparation)
    measure_one = lambda one, folder, written: measure_on_device(run, one, captures, preparation, isolation, repetitions, folder, written)
    return passes.run_all(chosen, repetitions, benchmark, measure_one, run.options), repetitions * len(chosen)


def warm_up(run, document, preparation):
    """Before the first pass: the device lists its plan once, and the warm-up picks from it."""
    if warmup.off(document):
        return
    arguments = session_arguments(run)
    planned = case_isolation.listed(run.device.instrument("CryptoBenchmark", *arguments, "-e", "log", "true"))
    run.device.pull_plan(preparation)
    cases = read_yaml(paths.Preparation(preparation).prepared).get("cases") or []
    warmup.run(run.device, "CryptoBenchmark", arguments, planned, cases, document, run.gate.session("warm-up"))


def host_cases(options, document, capture, trial, effective, benchmark, preparation, files, problems):
    repetitions, written = effective_view.process_repetitions(document), []
    if (document.get("run") or {}).get("passes"):
        print("warning: run.passes: only a --device run measures in passes; this run measures once per process")
    if effective_view.thermal_gate(document):
        warn("TEMPERATURE SET BUT DEVICE CAN'T POLL: host_runtime; running without it", problems)
    for repetition in range(1, repetitions + 1):
        into = measure_session.process_folder(benchmark, repetition, repetitions)
        measure_session.process_line(repetition, repetitions)
        (paths.Measurement(into).json).unlink(missing_ok=True)
        gradle_runner.run(f"{capture} {trial} {effective} {into} {preparation}", options.stacktrace, options.stream, main_class="BenchKt",
                          properties=bundled.gradle_properties(document.get(bundled.KEY) or []),
                          failed=lambda message: kept(into, message, problems))
        written.append(paths.Measurement(into).json)
        record(files, into, {"none"}, None)
    if repetitions > 1:
        passes.merge_runs(benchmark, written, options)
    return written


def kept(into, message, problems):
    """BenchKt writes each case's row as it finishes: when it dies, the rows it wrote are this run's, and its failure one problem line."""
    if not (paths.Measurement(into).json).is_file():
        fail(message)
    line = f"bench_failed: {one_line(message)}"
    print(f"warning: {line}")
    problems.append(line)


def collapse(files, preparation, repetitions):
    files.update(prepared=paths.Preparation(preparation).prepared, skipped=paths.Preparation(preparation).skipped)
    singles(files, repetitions)
