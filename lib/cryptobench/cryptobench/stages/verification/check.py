"""A --check run: every planned case called once through the real harness, on the host JVM or the device in one process, its output checked; check.yaml,
published beside a finished run or as a new device folder."""
import time

from cryptobench.shared.device import gradle_runner, instrumentation, reconnect
from cryptobench.shared.device.adb import NO_DEFAULT_PROFILER
from cryptobench.shared.device.plan import outputs, plan_pulls, push_plan
from cryptobench.shared.errors.failures import CommandError
from cryptobench.shared.results import layout as results_layout
from cryptobench.shared.results.publish_unit import Route, publish_unit
from cryptobench.stages.verification import known_answers as answers
from cryptobench.shared import paths
from cryptobench.shared.catalogue import vectors
from cryptobench.pipeline.took import elapsed
from cryptobench.shared.log.warn import warn
from cryptobench.shared.settings import bundled
from cryptobench.shared.document.document import read_yaml

# androidx.benchmark 1.5.0: one call per measureRepeated, no warm-up, no timing, no output file
DRY_RUN = ["-e", "androidx.benchmark.dryRunMode.enable", "true"]
CHECK = Route(paths.CHECK, lambda tree: {"check": tree.check.result},
              lambda tree: {"guide": tree.configuration.guide, "knownAnswers": tree.configuration.known_answers})


def require_check_run(options, device):
    """Before discovery: a --check that cannot run writes nothing."""
    if not (options.bench or device) or options.harness or options.interop:
        raise CommandError("--check: the cases are checked on a --bench (host JVM) or a --device run, without --harness or --interop")


def check_run(options, configuration, device, root, discovered, located, suite=None):
    """discovered(root, stage) is the route's discovery with guide.yaml beside effective.yaml, located discovery's: both run inside this stage's staging."""
    with results_layout.staged(root) as stage:
        found = discovered(root, stage)
        effective, capture, trial = found.effective, found.capture, found.trial
        into = paths.RunTree(stage).check.root
        into.mkdir(parents=True)
        known_answers = answers.write_known_answers(effective, capture, configuration)
        started = time.monotonic()
        if device:
            on_device(device, options, effective, capture, trial, known_answers, into)
        else:
            on_host(options, effective, capture, trial, known_answers, into)
        elapsed("end-to-end check", started)
        failed = summary(paths.CheckFolder(into).result)
        results = publish_unit(root, stage, found, CHECK, mode="device" if device else "host", configuration=configuration,
                               discovery_mode=options.discovery, located=located, suite=suite)
    if failed:
        raise CommandError(f"check_failed: {failed} cases failed or errored, see {paths.RunTree(results).check.result}")


def on_host(options, effective, capture, trial, known_answers, into):
    gradle_runner.run(f"{capture} {trial} {effective} {known_answers} {into}", options.stacktrace, options.stream, main_class="CheckKt",
                      properties=bundled.gradle_properties(bundled.recorded(effective)))


def on_device(device, options, effective, capture, trial, known_answers, into):
    waits = reconnect.Reconnect.of(device, options)
    waits.retried(lambda: push_plan(device, effective, paths.Configuration.holding(effective).guide, capture, trial, known_answers), "the plan push")
    suppressed = ["-e", "androidx.benchmark.suppressErrors", options.suppress_errors] if options.suppress_errors else []
    row = instrumentation.Instrumented("EndToEndCheck", cleared=outputs(device, (paths.CHECK_RESULT,)),
                                       pulled=((f"{device.files}/{paths.CHECK_RESULT}", paths.CheckFolder(into).result),
                                               *plan_pulls(device, paths.CheckFolder(into).preparation.root)))
    instrumentation.run(device, waits, row, *NO_DEFAULT_PROFILER, *DRY_RUN, *suppressed)


def summary(result):
    """Prints the outcome and per-oracle counts and every failed case; returns how many failed or errored."""
    document = read_yaml(result)
    counts = document["summary"]
    print("check:     " + ", ".join(f"{n} {outcome}" for outcome, n in counts["outcomes"].items()) + f" of {counts['cases']} cases")
    for oracle, verdicts in counts["oracles"].items():
        print(f"check:     {oracle}: " + ", ".join(f"{n} {verdict}" for verdict, n in verdicts.items()))
    bad = [case for case in document["cases"] if case["outcome"] in ("fail", "error")]
    for case in bad:
        reasons = case.get("reason") or "; ".join(f"{name}: {v.get('reason')}" for name, v in (case.get("oracles") or {}).items() if v["verdict"] == "fail")
        print(f"check:     {case['outcome']} {case['id']}: {reasons}")
    lines, compared = vectors.coverage(document["cases"])
    for line in lines:
        print(f"check:     {line}")
    if not compared:
        warn("no_known_vector_applied: no case was compared with a known answer; list vectors in the guide entries")
    return len(bad)
