"""A --harness run: perf-repair's scopes generated, interop-checked and measured on the device, original and patched."""
import pathlib, time

import effective_view, energy_stage
from device.identity import capture_id
from energy_session import EnergySession
from failure import fail
from repo import ROOT
from results import layout as results_layout
from results.manifest import manifest
from scope import generate as scope_generate
from scope import results as scope_results
from scope.harness import HarnessError
from session import energy_hook, passes, warmup
from session import measure as measure_session
from stages.discover import discover
from stages.measuring import (Measuring, convert, energy_preflight, gated, pass_arguments, push, record, session_arguments, singles,
                              thermal_flag, timed_hooks)
from stages.took import elapsed


def generate_scopes(options, scoped):
    started = time.monotonic()
    plan, compiled = scope_generate.generate(options.harness, ROOT, scoped)
    elapsed(f"generate and compile {len(compiled)} scopes", started)
    print(f"wrote:     {plan}")
    if not compiled:
        fail(f"no_scope_compiled: every scope is not_compilable or not_measurable, see {plan}")
    return plan


def require_harness_device(harness, capture):
    """A harness belongs to one device's folder; another device's numbers there would read as that device's."""
    import yaml
    built_for = harness.parent.parent / results_layout.MANIFEST
    if built_for.is_file():
        wanted, attached = (yaml.safe_load(built_for.read_text()) or {}).get("deviceId"), capture_id(capture)
        if wanted != attached:
            fail(f"harness_other_device: {harness} was built for {wanted}, the attached device is {attached}")


def measure_scopes(options, configuration, device, results, scoped, plan):
    """Interop check in one process, then the measured scopes through the device session; the files and problems for the manifest."""
    discovery, effective, capture, trial, files = discover(options, configuration, device, results)
    require_harness_device(pathlib.Path(options.harness).resolve(), capture)
    document = effective_view.read(effective)["document"]
    run_capture = energy_stage.capture(document.get("run"))
    if run_capture == "dry":
        fail("not_supported: run.harness.energy.capture dry with --harness; use measured or none")
    session, problems = EnergySession(device), []
    source = energy_stage.source(effective, options.energy_python, options.stacktrace)
    preflight = (lambda: energy_preflight(options, source, session, discovery, files)) if run_capture == "measured" else None
    push(device, options, [effective, capture, trial], preflight)
    started = time.monotonic()
    print("measure:   ScopedInterop on the device")
    interop = device.check_scopes(scoped)
    record, measured = scope_results.merge(plan, interop)
    files.update(scopedPlan=plan, scopedInterop=interop)
    for scope in record["scopes"]:
        print(f"scope:     {scope['id']} {scope['status']}" + (f": {scope['reason']}" if scope.get("reason") else "")
              + (f" ({scope['interop'].get('reason')})" if scope.get("interop", {}).get("reason") else ""))
    if measured:
        prepared = scope_results.prepared(record, measured, effective, scoped / "prepared.yaml")
        run = Measuring(device, session, source, options, discovery, files, problems, effective_view.throttle_sleep(document),
                        effective_view.case_cooldown(document))
        cases = tuple(case for scope in measured for case in scope["cases"])
        import yaml
        arguments = session_arguments(run, document)
        run = gated(run, document)
        warmup.run(device, "ScopedBenchmark", arguments, list(cases), yaml.safe_load(prepared.read_text())["cases"], document)
        scoped_passes(run, document, {run_capture}, prepared, cases, scoped)
    elapsed("interop check and measure", started)
    return files, problems


def scoped_passes(run, document, captures, prepared, cases, scoped):
    if run.gate is None:
        run = gated(run, document)
    chosen, repetitions, isolation = passes.read(document, captures), effective_view.scoped_repetitions(document), effective_view.isolation(document)
    measure_one = lambda one, folder, written: measure_scoped(run, one, captures, prepared, cases, isolation, repetitions, folder, written)
    written = passes.run_all(chosen, repetitions, scoped, measure_one, run.options)
    if written:
        run.files["processes"] = written
    singles(run.files, repetitions * len(chosen))
    run.files["scoped"] = scoped / "benchmark.json"
    print(f"wrote:     {run.files['scoped']}")


def measure_scoped(run, one, captures, prepared, cases, isolation, repetitions, folder, written):
    device, captures = run.device, one.captures(captures)
    hooks = timed_hooks(run, one, isolation)
    if "measured" in captures:
        hooks.insert(0, energy_hook.EnergyCapture(run.source, run.session, captures, run.discovery, prepared.parent, run.problems, None))

    def converted(process):
        joules = process.into / "energy.json"
        joined = f" {joules}" if joules.is_file() else ""
        convert(run, f"{process.data} {prepared} {process.into}{joined}{one.convert_flags()}{thermal_flag(process)}")
        written.append(process.into / "benchmark.json")
        record(run.files, process.into, captures, device)

    arguments = pass_arguments(run, one)
    plan = measure_session.Plan("ScopedBenchmark", arguments, cases=cases, named=True,
                                order=measure_session.alternating, pull_plan=lambda process: device.pull_pins(process.into), after_process=converted)
    measure_session.run_session(device, plan, repetitions, isolation, hooks, folder, run.problems)


def harness_run(options, configuration, device, results):
    try:
        with results_layout.kept_until_replaced(results / "scoped") as scoped:
            try:
                plan = generate_scopes(options, scoped)
                files, problems = measure_scopes(options, configuration, device, results, scoped, plan)
            except (HarnessError, scope_generate.GenerateError) as error:
                fail(str(error))
            manifest(results, "device", configuration, files, problems)
    finally:
        scope_generate.clean(ROOT)


def measured_folder(options):
    if options.results:
        fail("--results: a --harness run writes measured/ beside its harness.yaml")
    measured = pathlib.Path(options.harness).resolve().parent / "measured"
    results_layout.warn_if_temp(measured)
    return measured
