import importlib, subprocess, sys

import pytest
import yaml

import pipeline  # noqa: E402
from cryptobench.shared.device import timeouts  # noqa: E402
from cryptobench.shared.errors.coded import Coded  # noqa: E402
from cryptobench.shared.device.adb import DeviceError  # noqa: E402

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
    (DeviceError("no_device: x"), "no_device: x"),
    (timeouts.StepTimeout("timeout: adb ran past 1 s: adb"), "timeout: adb ran past 1 s: adb"),
    (subprocess.CalledProcessError(2, ["python3", "analyze.py"]), "subprocess_failed: python3 analyze.py exited 2"),
    (KeyError("files"), "internal_error: KeyError: 'files'"),
    (yaml.YAMLError("bad\nyaml"), "internal_error: YAMLError: bad yaml"),
])
def test_an_error_the_run_did_not_survive_is_one_line(error, line):
    assert pipeline.failure_line(error) == line


KNOWN = [
    "cryptobench.shared.device.adb.DeviceError", "cryptobench.shared.device.identity.DeviceIdError", "cryptobench.shared.device.capture.CaptureError", "cryptobench.shared.errors.failures.EnergyError",
    "cryptobench.shared.settings.bundled.BundledError", "cryptobench.stages.configuration.config_check.ConfigCheckError", "scope.results.ScopeResultError", "scope.code_digest.CodeDigestError",
    "cryptobench.shared.device.timeouts.StepTimeout", "session.dynamic_temperature.Terminated", "cryptobench.shared.errors.input_error.InputError",
    "cryptobench.shared.errors.failures.CommandError"]


def _class(name):
    module, _, attribute = name.rpartition(".")
    return getattr(importlib.import_module(module), attribute)


def test_the_known_failures_are_the_classes_marked_coded():
    assert sorted(f"{c.__module__}.{c.__name__}" for c in Coded.__subclasses__()) == sorted(KNOWN)


def test_a_marked_failure_carries_the_code_its_message_starts_with():
    assert (DeviceError("no_device: x").code, DeviceError("adb exited 1").code) == ("no_device", None)


@pytest.mark.parametrize("known", [_class(name) for name in KNOWN], ids=lambda c: c.__name__)
def test_a_known_failure_is_its_own_message_unchanged(known):
    assert pipeline.failure_line(known("some_code: a  spaced   message")) == "some_code: a  spaced   message"


def test_a_known_failure_keeps_its_line_breaks_and_length():
    long = "device_failed: " + "x" * 600 + "\nsecond line"
    assert pipeline.failure_line(DeviceError(long)) == long


def test_an_unknown_failure_is_one_line_cut_at_500_characters():
    line = pipeline.failure_line(RuntimeError("y" * 600 + "\nz"))
    assert line == "internal_error: RuntimeError: " + ("y" * 600 + " z")[:500]


def test_fail_prints_one_error_line_on_stderr_and_exits_1(capsys):
    with pytest.raises(SystemExit) as stopped:
        pipeline.fail("some_code: detail")
    assert stopped.value.code == 1 and capsys.readouterr() == ("", "error: some_code: detail\n")
