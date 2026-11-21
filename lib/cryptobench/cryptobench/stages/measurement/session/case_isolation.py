"""isolation: case: one instrumentation process per case, so a case that kills its process loses only itself."""
import re

from cryptobench.shared import paths
from cryptobench.shared.device import instrumentation, timeouts
from cryptobench.shared.errors.failures import ALL_CASES_SKIPPED, AllSkipped
from cryptobench.shared.errors.line import one_line
from cryptobench.shared.device.adb import ONE_PASSED, PASSED, DeviceError, DeviceLost
from cryptobench.shared.results import skipped
from cryptobench.stages.measurement.session import skips

CASE_ARGUMENT = "case"   # CaseFilter.ARGUMENT
LISTED = re.compile(r"^INSTRUMENTATION_STATUS: test=measure\[(.+)\]\s*$", re.M)
REFUSED_PLAN = "refused_plan:"   # RefusedPlanException


def listed(output):
    """The timed cases the device planned, in its order: AndroidJUnitRunner's -e log true lists them and runs none."""
    return list(dict.fromkeys(LISTED.findall(output)))


def planned(device, test_class, arguments, plan_skips):
    """The timed cases the device planned, in its order. A listing that failed on refused_plan, whose skipped.yaml (plan_skips(): the plan pulled,
    that document) holds only final skips, is AllSkipped; any other failed listing with no case is the device's report."""
    output = instrumentation.once(device, instrumentation.Instrumented(test_class, passed=None), *arguments, "-e", "log", "true")
    cases = listed(output)
    if cases or PASSED.search(output):
        return cases
    records = skipped.records(recorded(plan_skips)) if REFUSED_PLAN in output else []
    if records and all(skips.coded(record) for record in records):
        for case, code in dict(skips.coded(record) for record in records).items():
            print(skips.line(case, code))
        raise AllSkipped(f"{ALL_CASES_SKIPPED}: every case of {test_class} is refused by the plan check: {len(records)} skips, listed in {paths.SKIPPED}")
    raise DeviceError(f"{test_class} planned no case on the device:\n{device.report(output)}")


def recorded(plan_skips):
    try:
        return plan_skips()
    except DeviceLost:
        raise
    except DeviceError:
        return {}


def launch_case(device, test_class, arguments, case, pulled):
    """None, or the failure line; the case's benchmarkData, when the device wrote one, stays at pulled for the rules to judge."""
    row = instrumentation.Instrumented(test_class, cleared=(device.data,), passed=ONE_PASSED)
    try:
        instrumentation.once(device, row, *arguments, "-e", CASE_ARGUMENT, case, step="case")
    except timeouts.StepTimeout as error:
        # killing adb leaves the test running on the device; the next case must not start beside it
        device.force_stop()
        return f"case_failed: {case}: {error}"
    except instrumentation.Failed as failed:
        return f"case_failed: {case}: {one_line(device.report(failed.output) or 'no output')}"
    pulled.unlink(missing_ok=True)
    device.pull_optional(device.data, pulled)
    return None
