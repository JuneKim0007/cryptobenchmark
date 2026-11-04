"""isolation: case: one instrumentation process per case, so a case that kills its process loses only itself."""
import json, re

import timeouts

CASE_ARGUMENT = "case"   # CaseFilter.ARGUMENT
LISTED = re.compile(r"^INSTRUMENTATION_STATUS: test=measure\[(.+)\]\s*$", re.M)
PASSED = re.compile(r"^OK \(1 test\)", re.M)


def listed(output):
    """The timed cases the device planned, in its order: AndroidJUnitRunner's -e log true lists them and runs none."""
    return list(dict.fromkeys(LISTED.findall(output)))


def merged(documents):
    """One benchmarkData.json from one per process: the first process's context, every process's benchmarks."""
    return {"context": documents[0].get("context") or {},
            "benchmarks": [benchmark for document in documents for benchmark in document.get("benchmarks") or []]}


def one_line(text):
    return " ".join(text.split())[:500] or "no output"


def measure_case(device, test_class, arguments, case, pulled):
    """(benchmarkData document or None, failure line or None) for one case in its own process."""
    device.shell(f"rm -f {device.data}")
    pulled.unlink(missing_ok=True)
    try:
        output = device.instrument(test_class, *arguments, "-e", CASE_ARGUMENT, case, step="case")
    except timeouts.StepTimeout as error:
        # killing adb leaves the test running on the device; the next case must not start beside it
        device.force_stop()
        return None, f"case_failed: {case}: {error}"
    if not PASSED.search(output):
        return None, f"case_failed: {case}: {one_line(device.report(output))}"
    if device.run("pull", device.data, str(pulled), check=False).returncode != 0 or not pulled.is_file():
        return None, f"case_failed: {case}: no benchmarkData.json after a passing run"
    document = json.loads(pulled.read_text())
    pulled.unlink()
    return document, None
