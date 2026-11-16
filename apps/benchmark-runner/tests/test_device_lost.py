"""A lost adb transport mid-run (the 2026-11-15 pilot: `device unauthorized`): waited for, the same case held and launched again,
never a failed case; past the bound the run stops."""
import json, time, types

import pytest

from cryptobench.shared.device import timeouts
from cryptobench.shared.device import adb as device_module
from fake_phone import Phone
from test_device_benchmark_flow import OPTIONS, measured
from test_thermal_gate import GATE

UNAUTHORIZED = "adb: device unauthorized.\nThis adb server's $ADB_VENDOR_KEYS is not set\n"
SKIN = """Thermal Status: 0
HAL Ready: true
Current temperatures from HAL:
\tTemperature{mValue=30.0, mType=3, mName=VIRTUAL-SKIN, mStatus=0}
"""
# the pilot's case: the transport dropped inside am instrument, which printed only the test's start
CUT = "INSTRUMENTATION_STATUS: numtests=1\nINSTRUMENTATION_STATUS_CODE: 1\n"


class LosingPhone(Phone):
    """Drops the transport inside the instrumentation of `drop`; every adb call then goes through the real Device.run until
    `polls` adb get-state answers have passed."""

    def __init__(self, folder, drop, polls, **options):
        super().__init__(folder, thermal=SKIN, **options)
        self.drop, self.polls, self.offline, self.states = drop, polls, False, []

    def run(self, *arguments, check=True):
        if self.offline:
            return device_module.Device.run(self, *arguments, check=check)
        return super().run(*arguments, check=check)

    def shell(self, command):
        if self.offline:
            return device_module.Device.shell(self, command)
        return super().shell(command)

    def pull(self, remote, local):
        if self.offline:
            return device_module.Device.pull(self, remote, local)
        return super().pull(remote, local)

    def instrument(self, test_class, *arguments, step="instrument"):
        if self.offline:
            return device_module.Device.instrument(self, test_class, *arguments, step=step)
        if self.drop in arguments:
            self.drop, self.offline = None, True
            self.log.append(f"instrument {test_class} dropped")
            return CUT
        return super().instrument(test_class, *arguments, step=step)

    def answer(self, _step, command, **_options):
        if command[1] == "get-state":
            self.states.append(self.polls)
            if self.polls == 0:
                self.offline = False
                return types.SimpleNamespace(returncode=0, stdout="device\n", stderr="")
            self.polls -= 1
        return types.SimpleNamespace(returncode=1, stdout="", stderr=UNAUTHORIZED)


class Clock:
    def __init__(self, monkeypatch):
        self.now = 0.0
        monkeypatch.setattr(time, "monotonic", lambda: self.now)
        monkeypatch.setattr(time, "sleep", self.sleep)

    def sleep(self, seconds):
        self.now += seconds


def lost_run(tmp_path, monkeypatch, polls, wait_minutes=1):
    Clock(monkeypatch)
    phone = LosingPhone(tmp_path, "b", polls, cases=("a", "b", "c", "d"))
    monkeypatch.setattr(timeouts, "run", phone.answer)
    monkeypatch.setattr("test_device_benchmark_flow.OPTIONS", types.SimpleNamespace(**{**vars(OPTIONS), "reconnect_wait_minutes": wait_minutes,
                                                                                         "reconnect_poll_seconds": 10}))
    return phone, measured(tmp_path, monkeypatch, {"isolation": "case", "thermalGate": GATE, "launchRetries": 1}, phone=phone)


def test_the_pilots_lost_transport_is_waited_out_and_the_same_case_runs_again(tmp_path, monkeypatch, capsys):
    phone, (_phone, _files, problems, results) = lost_run(tmp_path, monkeypatch, polls=3)
    assert not [p for p in problems if p.startswith(("case_failed", "temperature_unreadable", "not_measured"))]
    launched = [s for s in phone.log if s.startswith("instrument ")]
    assert launched == ["instrument CryptoBenchmark a", "instrument CryptoBenchmark dropped", "instrument CryptoBenchmark b",
                        "instrument CryptoBenchmark c", "instrument CryptoBenchmark d"]
    assert phone.states == [3, 2, 1, 0]
    assert [b["name"] for b in json.loads((results / "benchmark/benchmarkData.json").read_text())["benchmarks"]] == [
        "measure[a]", "measure[b]", "measure[c]", "measure[d]"]
    out = capsys.readouterr().out
    assert "device:    back after 30 s; the hold and launch of b again" in out and "device_lost: adb shell " in out


def test_a_device_still_gone_past_the_bound_stops_the_run_and_keeps_the_cases_before(tmp_path, monkeypatch):
    with pytest.raises(Exception) as stopped:
        lost_run(tmp_path, monkeypatch, polls=10**6, wait_minutes=1)
    assert type(stopped.value).__name__ == "DeviceGone" and str(stopped.value).startswith("device_lost: ")
    assert "not back after 60 s" in str(stopped.value) and str(stopped.value).endswith("run stopped")
    data = tmp_path / "results/benchmark/benchmarkData.json"
    assert [b["name"] for b in json.loads(data.read_text())["benchmarks"]] == ["measure[a]"]


def test_any_adb_call_that_meets_a_lost_transport_is_device_lost(tmp_path, monkeypatch):
    device = device_module.Device(tmp_path, False, False)
    answers = iter([types.SimpleNamespace(returncode=1, stdout="", stderr="error: device offline\n")])
    monkeypatch.setattr(timeouts, "run", lambda *_a, **_o: next(answers))
    with pytest.raises(device_module.DeviceLost, match=r"^device_lost: adb pull /x y: device offline$"):
        device.run("pull", "/x", "y", check=False)


def test_a_cut_instrumentation_with_the_device_gone_is_device_lost_not_a_failed_test(tmp_path, monkeypatch):
    device = device_module.Device(tmp_path, False, False)
    answers = {"instrument": types.SimpleNamespace(returncode=0, stdout=CUT, stderr=""),
               "get-state": types.SimpleNamespace(returncode=1, stdout="", stderr="error: no devices/emulators found\n")}
    monkeypatch.setattr(timeouts, "run", lambda _step, command, **_o: answers["instrument" if "instrument" in command else "get-state"])
    with pytest.raises(device_module.DeviceLost, match="device_lost: adb get-state after am instrument CryptoBenchmark: no answer"):
        device.instrument("CryptoBenchmark", "-e", "case", "a", step="case")
