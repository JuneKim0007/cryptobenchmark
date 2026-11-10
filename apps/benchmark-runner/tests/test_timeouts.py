import subprocess, sys

import pytest
import yaml

import pipeline  # noqa: E402
import timeouts  # noqa: E402

SLEEP = [sys.executable, "-c", "import time; time.sleep(30)"]


def test_a_step_past_its_ceiling_is_a_coded_error_not_a_hang(monkeypatch):
    monkeypatch.setitem(timeouts.SECONDS, "adb", 0.2)
    with pytest.raises(timeouts.StepTimeout) as expired:
        timeouts.run("adb", SLEEP)
    assert str(expired.value).startswith("timeout: adb ran past 0.2 s: ")


def test_a_streamed_step_is_killed_at_its_ceiling(monkeypatch):
    monkeypatch.setitem(timeouts.SECONDS, "instrument", 0.2)
    process = subprocess.Popen(SLEEP, stdout=subprocess.PIPE, text=True)
    with pytest.raises(timeouts.StepTimeout):
        with timeouts.watched("instrument", process, SLEEP):
            process.stdout.read()
            process.wait()


def test_a_step_inside_its_ceiling_returns_its_result():
    assert timeouts.run("adb", [sys.executable, "-c", "print(1)"], capture_output=True, text=True).stdout == "1\n"


@pytest.mark.parametrize("error, line", [
    (pipeline.DeviceError("no_device: x"), "no_device: x"),
    (timeouts.StepTimeout("timeout: adb ran past 1 s: adb"), "timeout: adb ran past 1 s: adb"),
    (subprocess.CalledProcessError(2, ["python3", "analyze.py"]), "subprocess_failed: python3 analyze.py exited 2"),
    (KeyError("files"), "internal_error: KeyError: 'files'"),
    (yaml.YAMLError("bad\nyaml"), "internal_error: YAMLError: bad yaml"),
])
def test_an_error_the_run_did_not_survive_is_one_line(error, line):
    assert pipeline.failure_line(error) == line


def test_the_known_failures_are_these_classes_in_this_order():
    assert [f"{c.__module__}.{c.__name__}" for c in pipeline.KNOWN] == [
        "device.adb.DeviceError", "device.identity.DeviceIdError", "device.capture.CaptureError", "sources.runner.EnergyError",
        "bundled.BundledError", "stages.config_check.ConfigCheckError", "scope.results.ScopeResultError", "scope.code_digest.CodeDigestError",
        "timeouts.StepTimeout", "session.dynamic_temperature.Terminated", "cryptobench.coded.InputError"]


@pytest.mark.parametrize("known", pipeline.KNOWN, ids=lambda c: c.__name__)
def test_a_known_failure_is_its_own_message_unchanged(known):
    assert pipeline.failure_line(known("some_code: a  spaced   message")) == "some_code: a  spaced   message"


def test_a_known_failure_keeps_its_line_breaks_and_length():
    long = "device_failed: " + "x" * 600 + "\nsecond line"
    assert pipeline.failure_line(pipeline.DeviceError(long)) == long


def test_an_unknown_failure_is_one_line_cut_at_500_characters():
    line = pipeline.failure_line(RuntimeError("y" * 600 + "\nz"))
    assert line == "internal_error: RuntimeError: " + ("y" * 600 + " z")[:500]


def test_fail_prints_one_error_line_on_stderr_and_exits_1(capsys):
    with pytest.raises(SystemExit) as stopped:
        pipeline.fail("some_code: detail")
    assert stopped.value.code == 1 and capsys.readouterr() == ("", "error: some_code: detail\n")
