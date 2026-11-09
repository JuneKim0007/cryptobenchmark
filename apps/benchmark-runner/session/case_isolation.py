"""isolation: case: one instrumentation process per case, so a case that kills its process loses only itself."""
import re

import timeouts
from device.adb import ONE_PASSED

CASE_ARGUMENT = "case"   # CaseFilter.ARGUMENT
LISTED = re.compile(r"^INSTRUMENTATION_STATUS: test=measure\[(.+)\]\s*$", re.M)


def listed(output):
    """The timed cases the device planned, in its order: AndroidJUnitRunner's -e log true lists them and runs none."""
    return list(dict.fromkeys(LISTED.findall(output)))


def one_line(text):
    return " ".join(text.split())[:500] or "no output"


def launch_case(device, test_class, arguments, case, pulled):
    """None, or the failure line; the case's benchmarkData stays at pulled."""
    device.shell(f"rm -f {device.data}")
    try:
        output = device.instrument(test_class, *arguments, "-e", CASE_ARGUMENT, case, step="case")
    except timeouts.StepTimeout as error:
        # killing adb leaves the test running on the device; the next case must not start beside it
        device.force_stop()
        return f"case_failed: {case}: {error}"
    if not ONE_PASSED.search(output):
        return f"case_failed: {case}: {one_line(device.report(output))}"
    if device.run("pull", device.data, str(pulled), check=False).returncode != 0 or not pulled.is_file():
        return f"case_failed: {case}: no benchmarkData.json after a passing run"
    return None
