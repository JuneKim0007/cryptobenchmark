"""run.warmup: a pre-flight run of a few cases once per device session, before the first pass; its output is deleted, never pulled or converted."""
import fnmatch, time

import timeouts
from session import case_isolation
from session import passes
from device import thermal
from device.adb import DeviceError
from session.measure import PASSED

DEFAULT_CASES = 3
WARMUP_PASS = "warmup"   # PassArguments: any pass but energy and allocation captures no energy


def settings(document):
    warmup = (document.get("run") or {}).get("warmup") or {}
    return int(warmup.get("iterations", 10)), list(warmup.get("jobs") or [])


def matches(rule, case):
    """A test-set rule against a prepared case: provider and type by name, name as a glob on the algorithm; case and spelling as written."""
    fields = (("provider", "provider"), ("type", "type"), ("name", "algorithm"))
    return all(rule.get(key) is None or fnmatch.fnmatch(str(case.get(field, "")).lower(), str(rule[key]).lower()) for key, field in fields)


def chosen(planned, cases, jobs):
    """The planned ids the rules select, in plan order; no rule means the plan's first few."""
    if not jobs:
        return planned[:DEFAULT_CASES]
    by_id = {case["id"]: case for case in cases}
    return [case for case in planned if any(matches(rule, by_id.get(case, {})) for rule in jobs)]


def run(device, test_class, arguments, planned, cases, document):
    """One process over the chosen cases; a failure warns and the session goes on. Returns the cases it ran."""
    iterations, jobs = settings(document)
    if iterations == 0:
        print("warm-up:   off (run.warmup.iterations 0)")
        return []
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
