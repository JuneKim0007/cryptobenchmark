"""The only place a timed run of a case starts: each attempt is held for temperature, launched between the hooks, then judged."""
from failure import one_line
from session import calibration, case_isolation, dynamic_temperature
from cryptobench.measure import equations as eq


def hooked_case(process, case, hooks, run_case):
    """A hook that fails around a case costs that case its result, a case_failed line, never the session; the hooks it started still close."""
    started, failure = [], None
    for hook in hooks:
        try:
            hook.before_case(process, case)
        except Exception as error:
            failure = hook_failed(case, hook, "before_case", error)
            break
        started.append(hook)
    failure = failure or run_case()
    for hook in reversed(started):
        try:
            hook.after_case(process, case, failure)
        except Exception as error:
            failure = failure or hook_failed(case, hook, "after_case", error)
    return failure


def hook_failed(case, hook, step, error):
    return f"case_failed: {case}: hook_failed: {type(hook).__name__}.{step}: {type(error).__name__}: {one_line(error)}"


def run_of_case(device, plan, process, case, hooks, pulled):
    """None, or the case's failure line. Heat discards the run and measures it again; anything else is retried, then the next case goes on."""
    gate, retries, discards = plan.gate, plan.retries, 0
    while True:
        if not gate.hold(case):
            return f"case_failed: {case}: temperature_unreadable"
        failure = hooked_case(process, case, hooks, lambda: case_isolation.launch_case(device, plan.test_class, plan.arguments, case, pulled))
        verdict = gate.verdict(case) if not failure else eq.IGNORED
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
        print(f"warning: {one_line(reason)}; measuring the case again, {retries} retries left")
