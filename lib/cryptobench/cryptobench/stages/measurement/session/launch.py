"""The only place a timed run of a case starts: each attempt is held for temperature, launched between the hooks, then judged."""
from cryptobench.shared.device.adb import DeviceLost
from cryptobench.shared import paths
from cryptobench.shared.errors.coded import code_in
from cryptobench.shared.errors.line import one_line
from cryptobench.stages.measurement.session import case_isolation, dynamic_temperature, skips
from cryptobench.stages.measurement.validation import rejected, rules
from cryptobench.stages.measurement import start_margin as eq
from cryptobench.shared.log.warn import warn


def hooked_case(process, case, hooks, run_case):
    """A hook that fails around a case costs that case its result, a case_failed line, never the session; the hooks it started still close."""
    started, failure = [], None
    for hook in hooks:
        try:
            hook.before_case(process, case)
        except DeviceLost:
            raise
        except Exception as error:
            failure = hook_failed(case, hook, "before_case", error)
            break
        started.append(hook)
    failure = failure or run_case()
    for hook in reversed(started):
        try:
            hook.after_case(process, case, failure)
        except DeviceLost:
            raise
        except Exception as error:
            failure = failure or hook_failed(case, hook, "after_case", error)
    return failure


def hook_failed(case, hook, step, error):
    return f"case_failed: {case}: hook_failed: {type(hook).__name__}.{step}: {type(error).__name__}: {one_line(error)}"


def run_of_case(device, plan, process, case, hooks, pulled):
    """None, or the case's failure line; a short energy window whose relaunch fails every retry keeps its short result (decision 32)."""
    short = []
    failure = attempts(device, plan, process, case, hooks, pulled, short)
    if failure and short:
        pulled.write_bytes(short[0])
        plan.sizing.kept_short(process, case, failure)
        return None
    return failure


def attempts(device, plan, process, case, hooks, pulled, short):
    """None, or the case's failure line. Heat discards the run and measures it again; a lost device is waited for and the same case held and
    launched again; a case the device's preparation skipped with a final code is case_skipped, never launched again; an attempt that fails
    a rule (validation/rules.py) moves to rejected/ and, like any other failure, is retried, then the next case goes on. Every launch
    again is one process.relaunched entry; short takes the bytes of a window launched again for being short."""
    gate, retries, discards, attempt = plan.gate, plan.retries, 0, 0
    # a short energy window is launched once more with more samples, outside the retries
    arguments, relaunched = plan.arguments, None
    again = lambda code: process.relaunched.append({"case": case, "attempt": attempt, "code": code})
    while True:
        attempt += 1
        try:
            if not gate.hold(case):
                return f"case_failed: {case}: temperature_unreadable"
            # the gate's start reading goes to the Thermal hook and its end reading comes back for the verdict, so a run is read once at each end
            process.start_reading, process.end_reading = gate.take_start(), None
            failure = hooked_case(process, case, hooks, lambda: case_isolation.launch_case(device, plan.test_class, arguments, case, pulled))
            verdict = gate.verdict(case, process.end_reading) if not failure else eq.IGNORED
        except DeviceLost as lost:
            pulled.unlink(missing_ok=True)
            again("device_lost")
            plan.reconnect.back(lost, f"the hold and launch of {case}")
            continue
        if verdict == dynamic_temperature.UNREADABLE:
            pulled.unlink(missing_ok=True)
            return f"case_failed: {case}: temperature_unreadable after the run"
        if verdict == eq.HOT:
            pulled.unlink(missing_ok=True)
            discards += 1
            if discards >= gate.discard_limit:
                return gate.discard_limit_reached(case)
            again("temperature_discarded")
            continue
        result = rules.Result(rejected.run_of(plan.unit, process.into, process.repetition), case, pulled, relaunched)
        findings = [] if failure else rules.check_case(result, plan.expectation.planned(paths.RunTree(plan.unit).preparation.prepared))
        failed = rules.failed(findings)
        if not failure and not failed:
            for finding in findings:
                print(f"note: {finding.code}: {finding.detail}")
            more = plan.sizing.sized(process, case, pulled, relaunched) if plan.sizing else None
            if more:
                short.append(pulled.read_bytes())
                again("short_window")
                arguments, relaunched = plan.sizing.arguments(more), more
                continue
            return None
        if failed:
            rejected.moved(plan.unit, result, attempt, failed)
        reason = failure or f"case_failed: {case}: {failed[0].code}: {failed[0].detail}"
        code = failure and plan.reconnect.retried(lambda: plan.refused(case), "the skip record read")
        if code:
            return skips.line(case, code)
        if retries == 0:
            return reason
        retries -= 1
        again(failed[0].code if failed else code_in(reason.split(f"{case}: ", 1)[-1]) or "case_failed")
        warn(f"{one_line(reason)}; measuring the case again, {retries} retries left")
