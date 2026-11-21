"""The benchmark of a plain run: on the device in passes and sessions, or on the host JVM."""
import functools
import re
import time

from cryptobench.shared.settings import bundled, effective_view
from cryptobench.shared.settings.effective_view import EnergyView, RunView
from cryptobench.shared.device import gradle_runner
from cryptobench.stages.measurement.energy import steps as energy_stage
from cryptobench.stages.measurement.energy.session import EnergySession
from cryptobench.shared.log.warn import warn
from cryptobench.shared.log.stdout import WROTE, say
from cryptobench.shared.errors.line import one_line
from cryptobench.shared.errors.failures import ALL_CASES_SKIPPED, AllSkipped, CommandError
from cryptobench.shared import paths
from cryptobench.shared.device import reconnect
from cryptobench.stages.measurement.session import blocks, case_isolation, energy_hook, passes, skips, variant_order, warmup, window
from cryptobench.stages.measurement.session import measure as measure_session
from cryptobench.stages.measurement.validation import expectation, report
from cryptobench.stages.measurement import case_files
from cryptobench.stages.measurement.measuring import (Measuring, convert, energy_end, energy_preflight, gate_opened, pass_arguments, pull_pins, record, session_arguments,
                                                         singles, thermal_flag, timed_hooks)
from cryptobench.shared.device.plan import clear_outputs, pull_plan, push, recorded_skips
from cryptobench.pipeline.took import elapsed
from cryptobench.shared.document.document import read_yaml

# the ignored keys host_cases names in their own line
OWN_LINES = ("run.passes", "run.thermalGate")
# EnergyDryBenchmark's Parameterized name: capture[<caseId>]
DRY_CASE = re.compile(r"^INSTRUMENTATION_STATUS: test=capture\[(.+)\]\s*$", re.M)


def measure_on_device(run, one, captures, preparation, repetitions, folder, written, measured_blocks, redo):
    device, captures = run.device, one.captures(captures)
    timed = captures - {"dry"}
    gate = run.gate.session(one.label, one.gate)
    hooks = timed_hooks(run, one, gate) if timed else []
    energy = None
    if captures - {"none"}:
        dry = lambda into, guarded: gate.hold("energy dry pass") and dry_pass(run.session, into, preparation, run.problems, guarded)
        energy = energy_hook.EnergyCapture(run.source, run.session, captures, run.discovery, preparation, run.problems, dry, bool(timed))
        hooks.insert(0, energy)

    def conversion(process, joules, into):
        joined = f" {joules}" if "measured" in captures and joules.is_file() else ""
        convert(run, f"{process.data} {paths.Preparation(preparation).prepared} {into}{joined}{one.convert_flags()}{thermal_flag(process)}")

    def again(process):
        """Into the staging folder; energy_end swaps the files in once every process succeeded."""
        at, staged = paths.Measurement(process.into), paths.Measurement(paths.Measurement(process.into).redo)
        energy.written(process, staged.energy)
        if not timed:
            return [(staged.energy, at.energy)]
        conversion(process, staged.energy, staged.root)
        return [(staged.energy, at.energy), (staged.json, at.json)]

    def converted(process):
        if timed:
            conversion(process, paths.Measurement(process.into).energy, process.into)
        held(process)
        if energy is not None and paths.Measurement(process.into).energy.is_file():
            redo.append((one, process.into, lambda: again(process)))

    def held(process):
        if timed:
            written.append(paths.Measurement(process.into).json)
        if sizing and process.samples:
            run.files.setdefault("energySamples", []).append(sizing.write(process, paths.Measurement(process.into).energy_samples))
        record(run.files, process.into, captures, device)

    def kept(process):
        if sizing:
            sizing.seeded(paths.Measurement(process.into).energy_samples)
        held(process)

    arguments = pass_arguments(run, one)
    sizing = window.MinWindow(one.min_window, one.samples, lambda samples: pass_arguments(run, one, samples)) if one.row.sizing == passes.MIN_WINDOW else None
    plan = measure_session.Plan("CryptoBenchmark", arguments, run.order, gate, run.retries, run.reconnect, run.unit,
                                expectation.of(run.record["run"], one.name), timed=bool(timed),
                                cleared=(paths.PREPARED, paths.SKIPPED), stale=(paths.Preparation(preparation).prepared, paths.Preparation(preparation).skipped),
                                pull_plan=lambda process: (pull_plan(device, preparation), pull_pins(device, process)), after_process=converted,
                                blocks=measured_blocks, kept=kept,
                                refused=lambda case: device_skips(device, preparation).get(case), sizing=sizing,
                                plan_skips=lambda: pulled_skips(device, preparation))
    measure_session.run_session(device, plan, repetitions, hooks, folder, run.problems)



def device_skips(device, preparation):
    """The final skips the device recorded so far, by case id."""
    return skips.recorded(recorded_skips(device, paths.Preparation(preparation).skipped))


def pulled_skips(device, preparation):
    """prepared.yaml and skipped.yaml pulled from the device; the skipped.yaml document."""
    pull_plan(device, preparation)
    return read_yaml(paths.Preparation(preparation).skipped)


def dry_pass(session, into, preparation, problems, guarded):
    """Beside a timed run its failure costs only energy; alone it is the whole measurement."""
    print("measure:   EnergyDryBenchmark inside a host trace session")
    at = paths.Measurement(into)
    step = lambda: dry_skips(session.dry_pass(paths.repo().energy_trace_config, at.dry_trace, at.energy_dry, preparation), at.energy_dry, preparation,
                             problems, alone=not guarded)
    energy_stage.guarded(problems, step) if guarded else step()


def dry_skips(output, calls, preparation, problems, alone):
    """A dry case the device's preparation skipped with a final code is one case_skipped line; alone, a pass that measured none and skipped every
    case is AllSkipped."""
    measured = read_yaml(calls) or {}
    final = skips.recorded(read_yaml(paths.Preparation(preparation).skipped))
    cases = list(dict.fromkeys(DRY_CASE.findall(output)))
    skipped = [case for case in cases if case not in measured and case in final]
    for case in skipped:
        print(skips.line(case, final[case]))
        problems.append(skips.line(case, final[case]))
    if alone and not measured and skipped and len(skipped) == len(cases):
        raise AllSkipped(f"{ALL_CASES_SKIPPED}: every case of EnergyDryBenchmark is a coded preparation skip: {len(skipped)} cases, listed in {paths.SKIPPED}")


def measure_cases(options, device, results, found, problems, require_energy, record, redo):
    """found is discovery's Discovered; require_energy is the entry point's check of the energy interpreter, passed in; it returns the interpreter the run uses;
    record: the run's record, every block's identity; redo: the restart's resume.RedoPlan."""
    benchmark, preparation = paths.RunTree(results).benchmark.root, paths.RunTree(results).preparation.root
    discovery, effective, capture, trial, files = found.discovery, found.effective, found.capture, found.trial, found.files
    started = time.monotonic()
    document = effective_view.read(effective)["document"]
    view, energy = RunView(document), EnergyView(document)
    repetitions, captures = view.process_repetitions, energy.captures
    timed = bool(captures - {"dry"})
    size = view.resume_block_runs
    in_blocks = lambda folder, label, boot: blocks.Blocks(folder, size, repetitions, record, document.get("runId"),
                                                          report.checker(results, folder, expectation.of(record["run"], label)), redo.of_pass(label), label, boot)
    if redo.findings:
        report.written(results, report.RESTART, redo.findings)
    if captures - {"none"} and not device:
        raise CommandError("energy: only a --device run captures energy; set harness.energy.capture none for --bench")
    if captures - {"none"}:
        # the effective config holds the captures a test set turned on, which the first check could not see
        options.energy_python = require_energy(energy.source, options.energy_python)
    order = variant_order.chosen(view.order_seed)[0]
    if device:
        waits = reconnect.Reconnect.of(device, options)
        print(waits.line())
        source = energy_stage.source(energy, options.energy_python, view.energy_idle_seconds, options.stacktrace)
        run = Measuring(device, EnergySession(device, waits), source, options, discovery, files, problems, order,
                        view.throttle_sleep, gate_opened(device, document, problems, waits), view.launch_retries, waits, results, record)
        try:
            written, processes = device_cases(run, document, [effective, paths.Configuration.holding(effective).guide, capture, trial], captures, benchmark,
                                              preparation, in_blocks)
        except AllSkipped as outcome:
            # nothing to measure is the run's outcome: the manifest keeps the plan files and the reason, no benchmark.json, exit 0
            print(outcome)
            problems.append(str(outcome))
            files.update(prepared=paths.Preparation(preparation).prepared, skipped=paths.Preparation(preparation).skipped)
            return False, [], repetitions
    else:
        written, processes = host_cases(options, document, capture, trial, effective, benchmark, preparation, files, problems,
                                        in_blocks(benchmark, None, lambda: None), order), repetitions
    say(WROTE, paths.Preparation(preparation).prepared)
    elapsed("prepare and measure", started)
    collapse(files, preparation, processes)
    return timed, written, repetitions


def device_cases(run, document, plan_files, captures, benchmark, preparation, in_blocks):
    """Every pass of the run on the device; the per-process files for the manifest and how many processes ran. in_blocks(pass folder, pass name,
    boot) is a pass's blocks.Blocks."""
    chosen, repetitions = passes.pass_views(RunView(document), captures), RunView(document).process_repetitions
    energy = next((one for one in chosen if one.captures(captures) - {"none"}), None)
    energy_step = (lambda: energy_preflight(run, energy.gate)) if energy else None
    run.reconnect.retried(lambda: push(run.device, run.options, plan_files, energy_step), "the plan push")
    run.reconnect.retried(lambda: warm_up(run, document, preparation), "the warm-up")
    boot = lambda: run.reconnect.retried(run.device.boot_id, "the boot id read")
    redo, pass_blocks = [], {}

    def measure_one(one, folder, written):
        pass_blocks[one] = in_blocks(one.folder(benchmark), one.name, boot)
        measure_on_device(run, one, captures, preparation, repetitions, folder, written, pass_blocks[one], redo)

    def finish():
        redone = energy_end(run, redo, energy.gate)
        for one, folders in redone.items():
            blocks.refreshed(pass_blocks[one], folders)
        return redone
    return passes.run_all(chosen, repetitions, benchmark, measure_one, run.options, finish if energy else None), repetitions * len(chosen)


def warm_up(run, document, preparation):
    """Before the first pass: the device lists its plan once, and the warm-up picks from it."""
    if warmup.off(document):
        return
    arguments = session_arguments(run)
    # a skipped.yaml an earlier run left must not answer this listing's refusal
    clear_outputs(run.device, (paths.PREPARED, paths.SKIPPED))
    planned = case_isolation.planned(run.device, "CryptoBenchmark", arguments, lambda: pulled_skips(run.device, preparation))
    pull_plan(run.device, preparation)
    cases = read_yaml(paths.Preparation(preparation).prepared).get("cases") or []
    warmup.run(run.device, "CryptoBenchmark", arguments, planned, cases, document, run.gate.session("warm-up"),
               lambda: run.reconnect.retried(lambda: device_skips(run.device, preparation), "the skip record read"))


def host_cases(options, document, capture, trial, effective, benchmark, preparation, files, problems, measured_blocks, order):
    """One BenchKt JVM per repetition, in measured_blocks, measuring in order(repetition, the listed cases); a block an earlier run recorded is
    kept, not measured again."""
    view = RunView(document)
    repetitions, written = view.process_repetitions, []
    if view.passes:
        warn("run.passes: only a --device run measures in passes; this run measures once per process")
    if effective_view.gate_scopes(document):
        warn("TEMPERATURE SET BUT DEVICE CAN'T POLL: host_runtime; running without it", problems)
    for path in effective_view.ignored_on_host(document):
        if path not in OWN_LINES:
            warn(f"ignored_on_host: {path} is set; only a --device run reads it")
    folder = lambda repetition: measure_session.process_folder(benchmark, repetition, repetitions)
    properties = bundled.gradle_properties(document.get(bundled.KEY) or [])

    # the first repetition measured lists once; a rerun that keeps every block lists nothing
    @functools.cache
    def listed():
        return gradle_runner.run(f"{capture} {trial} {effective} {preparation}", options.stacktrace, main_class="ListCasesKt", properties=properties)

    def measured(repetition):
        into = folder(repetition)
        measure_session.process_line(repetition, repetitions)
        (paths.Measurement(into).json).unlink(missing_ok=True)
        into.mkdir(parents=True, exist_ok=True)
        case_files.ordered(into, order(repetition, listed()))
        gradle_runner.run(f"{capture} {trial} {effective} {into} {preparation} {paths.Measurement(into).order}", options.stacktrace, options.stream,
                          main_class="BenchKt", properties=properties, failed=lambda message: kept(into, message, problems))
        held(into)

    def held(into):
        written.append(paths.Measurement(into).json)
        record(files, into, {"none"}, None)
    # a host run keeps no per-case files, so a restart never launches its cases again
    blocks.measured(measured_blocks, folder, measured, lambda repetition: held(folder(repetition)), None, problems)
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
