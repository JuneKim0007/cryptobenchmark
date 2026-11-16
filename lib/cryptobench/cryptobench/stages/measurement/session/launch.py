"""The only place a timed run of a case starts: each attempt is held for temperature, launched between the hooks, then judged."""
from cryptobench.shared.device.adb import DeviceLost
from cryptobench.shared.errors.line import one_line
from cryptobench.stages.measurement.session import calibration, case_isolation, dynamic_temperature
from cryptobench.stages.measurement import start_margin as eq
from cryptobench.pipeline.warn import warn


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
    """None, or the case's failure line. Heat discards the run and measures it again; a lost device is waited for and the same case held and
    launched again; anything else is retried, then the next case goes on."""
    gate, retries, discards = plan.gate, plan.retries, 0
    while True:
        try:
            if not gate.hold(case):
                return f"case_failed: {case}: temperature_unreadable"
            # the gate's start reading goes to the Thermal hook and its end reading comes back for the verdict, so a run is read once at each end
            process.start_reading, process.end_reading = gate.take_start(), None
            failure = hooked_case(process, case, hooks, lambda: case_isolation.launch_case(device, plan.test_class, plan.arguments, case, pulled))
            verdict = gate.verdict(case, process.end_reading) if not failure else eq.IGNORED
        except DeviceLost as lost:
            pulled.unlink(missing_ok=True)
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
            continue
        short = calibration.short_samples(pulled) if not failure else []
        if not failure and not short:
            for line in calibration.near_cap(pulled):
                print(line)
            return None
        reason = failure or f"case_failed: {case}: {short[0]}"
        if retries == 0:
            return reason
        retries -= 1
        warn(f"{one_line(reason)}; measuring the case again, {retries} retries left")
