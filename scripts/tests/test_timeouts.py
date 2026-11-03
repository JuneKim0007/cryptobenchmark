import pathlib, subprocess, sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
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


def test_every_step_has_a_ceiling_and_each_is_generous():
    assert all(seconds >= 600 for seconds in timeouts.SECONDS.values())
    assert timeouts.SECONDS["instrument"] >= 6 * 60 * 60
