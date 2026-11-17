"""The benchmark of a plain run: on the device in passes and sessions, or on the host JVM."""
import time

from cryptobench.shared.settings import bundled, effective_view
from cryptobench.shared.device import gradle_runner
from cryptobench.stages.measurement.energy import steps as energy_stage
from cryptobench.stages.measurement.energy.session import EnergySession
from cryptobench.pipeline.warn import warn
from cryptobench.shared.errors.line import one_line
from cryptobench.shared.errors.failures import CommandError
from cryptobench.shared import paths
from cryptobench.stages.measurement import resume
from cryptobench.stages.measurement.session import blocks, case_isolation, energy_hook, passes, reconnect, warmup
from cryptobench.stages.measurement.session import measure as measure_session
from cryptobench.stages.measurement.measuring import (Measuring, convert, energy_preflight, gated, pass_arguments, pull_pins, record, session_arguments,
                                                         singles, thermal_flag, timed_hooks)
from cryptobench.shared.device.plan import pull_plan, push
from cryptobench.pipeline.took import elapsed
from cryptobench.shared.document.document import read_yaml


def measure_on_device(run, one, captures, preparation, isolation, repetitions, folder, written, measured_blocks):
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
        held(process)

    def held(process):
        if timed:
            written.append(paths.Measurement(process.into).json)
        record(run.files, process.into, captures, device)

    arguments = pass_arguments(run, one)
    plan = measure_session.Plan("CryptoBenchmark", arguments, timed=bool(timed), order=run.order,
                                cleared=(paths.PREPARED, paths.SKIPPED), stale=(paths.Preparation(preparation).prepared, paths.Preparation(preparation).skipped),
                                pull_plan=lambda process: (pull_plan(device, preparation), pull_pins(device, process.into)), after_process=converted,
                                gate=gate, retries=run.retries, reconnect=run.reconnect, blocks=measured_blocks, kept=held)
    measure_session.run_session(device, plan, repetitions, isolation, hooks, folder, run.problems)


def dry_pass(session, into, preparation, problems, guarded):
    """Beside a timed run its failure costs only energy; alone it is the whole measurement."""
    print("measure:   EnergyDryBenchmark inside a host trace session")
    step = lambda: session.dry_pass(paths.repo().energy_trace_config, paths.Measurement(into).dry_trace, paths.Measurement(into).energy_dry, preparation)
    energy_stage.guarded(problems, step) if guarded else step()


def measure_cases(options, device, results, discovery, effective, capture, trial, files, problems, require_energy):
    """require_energy is the entry point's check of the energy interpreter, passed in."""
    benchmark, preparation = paths.RunTree(results).benchmark.root, paths.RunTree(results).preparation.root
    started = time.monotonic()
    document = effective_view.read(effective)["document"]
    repetitions, captures = effective_view.process_repetitions(document), energy_stage.captures(effective)
    timed = bool(captures - {"dry"})
    size, identity = effective_view.resume_block_runs(document), resume.run_identity(effective, capture, options.suppress_errors)
    in_blocks = lambda folder, label, boot: blocks.Blocks(folder, size, repetitions, identity, document.get("runId"), label, boot)
    if captures - {"none"} and not device:
        raise CommandError("energy: only a --device run captures energy; set harness.energy.capture none for --bench")
    if captures - {"none"}:
        # the effective config holds the captures a test set turned on, which the first check could not see
        require_energy(energy_stage.source_name(effective), options.energy_python)
    if device:
        waits = reconnect.Reconnect.of(device, options)
        print(waits.line())
        run = Measuring(device, EnergySession(device), energy_stage.source(effective, options.energy_python, options.stacktrace), options, discovery,
                        files, problems, effective_view.throttle_sleep(document), effective_view.case_cooldown(document), reconnect=waits)
        written, processes = device_cases(run, document, [effective, paths.Configuration.holding(effective).guide, capture, trial], captures, benchmark, preparation,
                                          in_blocks)
    else:
        written, processes = host_cases(options, document, capture, trial, effective, benchmark, preparation, files, problems,
                                        in_blocks(benchmark, None, lambda: None)), repetitions
    print(f"wrote:     {paths.Preparation(preparation).prepared}")
    elapsed("prepare and measure", started)
    collapse(files, preparation, processes)
    return timed, written, repetitions


def device_cases(run, document, plan_files, captures, benchmark, preparation, in_blocks):
    """Every pass of the run on the device; the per-process files for the manifest and how many processes ran. in_blocks(pass folder, pass name,
    boot) is a pass's blocks.Blocks."""
    chosen, repetitions = passes.read(document, captures), effective_view.process_repetitions(document)
    energy = any(one.captures(captures) - {"none"} for one in chosen)
    run = gated(run, document)
    energy_step = (lambda: energy_preflight(run.options, run.source, run.session, run.discovery, run.files)) if energy else None
    run.reconnect.retried(lambda: push(run.device, run.options, plan_files, energy_step), "the plan push")
    isolation = effective_view.isolation(document)
    run.reconnect.retried(lambda: warm_up(run, document, preparation), "the warm-up")
    boot = lambda: run.reconnect.retried(run.device.boot_id, "the boot id read")
    measure_one = lambda one, folder, written: measure_on_device(run, one, captures, preparation, isolation, repetitions, folder, written,
                                                                 in_blocks(one.folder(benchmark), one.name, boot))
    return passes.run_all(chosen, repetitions, benchmark, measure_one, run.options), repetitions * len(chosen)


def warm_up(run, document, preparation):
    """Before the first pass: the device lists its plan once, and the warm-up picks from it."""
    if warmup.off(document):
        return
    arguments = session_arguments(run)
    planned = case_isolation.listed(run.device.instrument("CryptoBenchmark", *arguments, "-e", "log", "true"))
    pull_plan(run.device, preparation)
    cases = read_yaml(paths.Preparation(preparation).prepared).get("cases") or []
    warmup.run(run.device, "CryptoBenchmark", arguments, planned, cases, document, run.gate.session("warm-up"))


def host_cases(options, document, capture, trial, effective, benchmark, preparation, files, problems, measured_blocks):
    """One BenchKt JVM per repetition, in measured_blocks; a block an earlier run recorded is kept, not measured again."""
    repetitions, written = effective_view.process_repetitions(document), []
    if (document.get("run") or {}).get("passes"):
        warn("run.passes: only a --device run measures in passes; this run measures once per process")
    if effective_view.thermal_gate(document):
        warn("TEMPERATURE SET BUT DEVICE CAN'T POLL: host_runtime; running without it", problems)
    if effective_view.order_seed(document) is not None:
        warn("run.orderSeed: only a --device run launches cases in an order; this run measures in the plan's order")
    folder = lambda repetition: measure_session.process_folder(benchmark, repetition, repetitions)

    def measured(repetition):
        into = folder(repetition)
        measure_session.process_line(repetition, repetitions)
        (paths.Measurement(into).json).unlink(missing_ok=True)
        gradle_runner.run(f"{capture} {trial} {effective} {into} {preparation}", options.stacktrace, options.stream, main_class="BenchKt",
                          properties=bundled.gradle_properties(document.get(bundled.KEY) or []),
                          failed=lambda message: kept(into, message, problems))
        held(into)

    def held(into):
        written.append(paths.Measurement(into).json)
        record(files, into, {"none"}, None)
    blocks.measured(measured_blocks, folder, measured, lambda repetition: held(folder(repetition)), problems)
    if repetitions > 1:
        passes.merge_runs(benchmark, written, options)
    return written


def kept(into, message, problems):
    """BenchKt writes each case's row as it finishes: when it dies, the rows it wrote are this run's, and its failure one problem line."""
    if not (paths.Measurement(into).json).is_file():
        raise CommandError(message)
    warn(f"bench_failed: {one_line(message)}", problems)


def collapse(files, preparation, repetitions):
    files.update(prepared=paths.Preparation(preparation).prepared, skipped=paths.Preparation(preparation).skipped)
    singles(files, repetitions)
