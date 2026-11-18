"""run.warmup: a pre-flight run of a few cases before the first pass of a device run; its output is deleted, never pulled or converted."""
import time

from cryptobench.shared.settings import effective_view
from cryptobench.shared.device import instrumentation, timeouts
from cryptobench.stages.measurement.session import case_isolation
from cryptobench.stages.measurement.session import dynamic_temperature, passes, skips
from cryptobench.stages.measurement.session.measure import COUNTED
from cryptobench.stages.measurement import thermal
from cryptobench.shared.device.adb import DeviceError, DeviceLost
from cryptobench.shared.device.plan import clear_outputs, outputs
from cryptobench.shared.errors.line import one_line
from cryptobench.shared.log.warn import warn

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


def run(device, test_class, arguments, planned, cases, document, gate=dynamic_temperature.Off(), skipped=lambda: {}):
    """One process over the chosen cases; a failure warns and the session goes on. skipped(): the device's final skips by case id
    (skips.py); a chosen case among them is left out and the choice made again. Returns the cases it warmed."""
    if off(document):
        return []
    iterations, jobs = settings(document)
    left_out = {case: code for case, code in skipped().items() if case in planned}
    while True:
        selected = chosen([case for case in planned if case not in left_out], cases, jobs)
        if not selected:
            warn("WARM-UP SKIPPED: run.warmup.jobs select no planned case" + (" that prepares" if left_out else "") + "; measuring without a warm-up")
            return []
        warmed = once(device, test_class, arguments, selected, iterations, gate, left_out, skipped)
        if warmed is not None:
            return warmed


def once(device, test_class, arguments, selected, iterations, gate, left_out, skipped):
    """The warmed cases; [] after a failure; None when every chosen case was a final skip, now in left_out."""
    if not gate.hold("warm-up"):
        warn("WARM-UP SKIPPED: temperature_unreadable; measuring without a warm-up")
        return []
    before, started = thermal.read(device), time.monotonic()
    named = ("-e", case_isolation.CASE_ARGUMENT, ",".join(selected), "-e", passes.PASS_ARGUMENT, WARMUP_PASS, "-e", passes.SAMPLES_ARGUMENT, str(iterations))
    output = ""
    row = instrumentation.Instrumented(test_class, cleared=outputs(device), clear_when=instrumentation.AFTER)
    try:
        output, failed = instrumentation.once(device, row, *arguments, *named, step="case"), None
    except DeviceLost:
        raise
    except instrumentation.Failed as error:
        output, failed = error.output, device.report(error.output)
    except (DeviceError, timeouts.StepTimeout) as error:
        device.force_stop()
        clear_outputs(device)
        failed = str(error)
    found = {case: code for case, code in skipped().items() if case in selected} if failed else {}
    after = thermal.read(device)
    for case, code in found.items():
        print(f"warm-up:   {skips.line(case, code)}")
    left_out.update(found)
    counted = COUNTED.search(output)
    if failed and not (found and counted and int(counted.group(2)) == len(found)):
        warn("WARM-UP FAILED, measuring anyway: " + one_line(failed, 300))
        return []
    warmed = [case for case in selected if case not in found]
    if not warmed:
        return None
    heat = (f"hottest {before.hottest:.1f} C before, {after.hottest:.1f} C after" if before.hottest is not None and after.hottest is not None
            else "temperature unavailable")
    print(f"warm-up:   {len(warmed)} cases x {iterations} samples in {time.monotonic() - started:.0f}s, a pre-flight check, not measured; {heat}")
    return warmed
