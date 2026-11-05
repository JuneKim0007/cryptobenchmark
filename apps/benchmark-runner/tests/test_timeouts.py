import pathlib, subprocess, sys

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
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
