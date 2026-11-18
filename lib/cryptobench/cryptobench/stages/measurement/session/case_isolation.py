"""isolation: case: one instrumentation process per case, so a case that kills its process loses only itself."""
import json
import re

from cryptobench.shared.device import instrumentation, timeouts
from cryptobench.shared.errors.line import one_line
from cryptobench.shared.device.adb import ONE_PASSED

CASE_ARGUMENT = "case"   # CaseFilter.ARGUMENT
LISTED = re.compile(r"^INSTRUMENTATION_STATUS: test=measure\[(.+)\]\s*$", re.M)
# androidx prefixes a result with the error ids it suppressed: EMULATOR_measure[...], DEBUGGABLE_EMULATOR_measure[...]
SUPPRESSED_PREFIX = re.compile(r"^(?:[A-Z][A-Z0-9-]*_)+(?=measure\[)")


def listed(output):
    """The timed cases the device planned, in its order: AndroidJUnitRunner's -e log true lists them and runs none."""
    return list(dict.fromkeys(LISTED.findall(output)))


def launch_case(device, test_class, arguments, case, pulled):
    """None, or the failure line; the case's benchmarkData stays at pulled."""
    row = instrumentation.Instrumented(test_class, cleared=(device.data,), passed=ONE_PASSED)
    try:
        instrumentation.once(device, row, *arguments, "-e", CASE_ARGUMENT, case, step="case")
    except timeouts.StepTimeout as error:
        # killing adb leaves the test running on the device; the next case must not start beside it
        device.force_stop()
        return f"case_failed: {case}: {error}"
    except instrumentation.Failed as failed:
        return f"case_failed: {case}: {one_line(device.report(failed.output) or 'no output')}"
    if not device.pull_optional(device.data, pulled):
        return f"case_failed: {case}: no benchmarkData.json after a passing run"
    named = _result_name(pulled)
    if SUPPRESSED_PREFIX.sub("", named) != f"measure[{case}]":
        pulled.unlink()
        return f"case_failed: {case}: result_mismatch: the pulled benchmarkData.json names {named}, not measure[{case}]; not stored"
    return None


def _result_name(pulled):
    """benchmarks[0].name of a pulled benchmarkData.json, or why there is none."""
    try:
        benchmarks = json.loads(pulled.read_text()).get("benchmarks") or []
        return benchmarks[0]["name"] if benchmarks else "no benchmark"
    except (ValueError, AttributeError, KeyError, TypeError) as error:
        return f"nothing readable ({type(error).__name__})"
