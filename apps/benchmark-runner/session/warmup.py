"""run.warmup: a pre-flight run of a few cases once per device session, before the first pass; its output is deleted, never pulled or converted."""
import time

import effective_view
import timeouts
from session import case_isolation
from session import passes
from device import thermal
from device.adb import PASSED, DeviceError

DEFAULT_CASES = 3
WARMUP_PASS = "warmup"   # PassArguments: any pass but energy and allocation captures no energy


def settings(document):
    return effective_view.required(document, "run.warmup.iterations"), effective_view.required(document, "run.warmup.jobs")


def matches(job, case):
    """A job is one effective entry :config resolved from run.warmup.jobs; its prepared cases carry the same names."""
    return (job["provider"], job["type"], job["name"], job.get("group")) == (case.get("provider"), case.get("type"), case.get("algorithm"), case.get("group"))


def chosen(planned, cases, jobs):
    """The planned ids the jobs select, in plan order; no job means the plan's first few."""
    if not jobs:
        return planned[:DEFAULT_CASES]
    by_id = {case["id"]: case for case in cases}
    return [case for case in planned if any(matches(rule, by_id.get(case, {})) for rule in jobs)]


def off(document):
    if settings(document)[0] == 0:
        print("warm-up:   off (run.warmup.iterations 0)")
        return True
    return False


def run(device, test_class, arguments, planned, cases, document):
    """One process over the chosen cases; a failure warns and the session goes on. Returns the cases it ran."""
    if off(document):
        return []
    iterations, jobs = settings(document)
    selected = chosen(planned, cases, jobs)
    if not selected:
        print("warning: WARM-UP SKIPPED: run.warmup.jobs select no planned case; measuring without a warm-up")
        return []
    before, started = thermal.read(device), time.monotonic()
    named = ("-e", case_isolation.CASE_ARGUMENT, ",".join(selected), "-e", passes.PASS_ARGUMENT, WARMUP_PASS, "-e", passes.SAMPLES_ARGUMENT, str(iterations))
    try:
        output = device.instrument(test_class, *arguments, *named, step="case")
        failed = None if PASSED.search(output) else device.report(output)
    except (DeviceError, timeouts.StepTimeout) as error:
        device.force_stop()
        failed = str(error)
    device.clear_outputs()
    after = thermal.read(device)
    if failed:
        print("warning: WARM-UP FAILED, measuring anyway: " + " ".join(failed.split())[:300])
        return []
    heat = (f"hottest {before.hottest:.1f} C before, {after.hottest:.1f} C after" if before.hottest is not None and after.hottest is not None
            else "temperature unavailable")
    print(f"warm-up:   {len(selected)} cases x {iterations} samples in {time.monotonic() - started:.0f}s, a pre-flight check, not measured; {heat}")
    return selected
