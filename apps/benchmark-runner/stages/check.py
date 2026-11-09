"""A --check run: every planned case called once through the real harness, on the host JVM or the device in one process, its output checked; check.yaml."""
import shutil, time

import yaml

import gradle_runner
from device.adb import NO_DEFAULT_PROFILER, PASSED, DeviceError, instrumentation_report
from failure import fail
from results.manifest import manifest
from stages import guide
from cryptobench.catalogue import vectors
from stages.discover import device_discover
from stages.took import elapsed
import bundled

FOLDER = "check"
RESULT = "check.yaml"   # CheckFile.NAME
# androidx.benchmark 1.5.0: one call per measureRepeated, no warm-up, no timing, no output file
DRY_RUN = ["-e", "androidx.benchmark.dryRunMode.enable", "true"]


def check_run(options, configuration, device, root):
    if not (options.bench or device) or options.harness or options.interop:
        fail("--check: the cases are checked on a --bench (host JVM) or a --device run, without --harness or --interop")
    results, (_, effective, capture, trial, files) = device_discover(options, configuration, device, root)
    into = results / FOLDER
    shutil.rmtree(into, ignore_errors=True)
    into.mkdir(parents=True)
    known_answers = guide.write_known_answers(effective, capture, configuration)
    files["knownAnswers"] = known_answers
    started = time.monotonic()
    if device:
        on_device(device, options, effective, capture, trial, known_answers, into)
    else:
        on_host(options, effective, capture, trial, known_answers, into)
    elapsed("end-to-end check", started)
    failed = summary(into / RESULT)
    manifest(results, "device" if device else "host", configuration, files | {"check": into / RESULT})
    if failed:
        fail(f"check_failed: {failed} cases failed or errored, see {into / RESULT}")


def on_host(options, effective, capture, trial, known_answers, into):
    gradle_runner.run(f"{capture} {trial} {effective} {known_answers} {into}", options.stacktrace, options.stream, main_class="CheckKt",
                      properties=bundled.gradle_properties(bundled.recorded(effective)))


def on_device(device, options, effective, capture, trial, known_answers, into):
    device.clear_outputs((RESULT,))
    device.push_plan(effective, guide.file_beside(effective), capture, trial, known_answers)
    suppressed = ["-e", "androidx.benchmark.suppressErrors", options.suppress_errors] if options.suppress_errors else []
    output = device.instrument("EndToEndCheck", *NO_DEFAULT_PROFILER, *DRY_RUN, *suppressed)
    if not PASSED.search(output):
        raise DeviceError("EndToEndCheck failed on the device:\n" + instrumentation_report(output))
    device.pull(f"{device.files}/{RESULT}", into / RESULT)
    device.pull_plan(into / "preparation")


def summary(result):
    """Prints the outcome and per-oracle counts and every failed case; returns how many failed or errored."""
    document = yaml.safe_load(result.read_text())
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
        print("warning: no_known_vector_applied: no case was compared with a known answer; list vectors in the guide entries")
    return len(bad)
