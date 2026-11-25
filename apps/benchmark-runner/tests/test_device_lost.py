"""A lost adb transport mid-run (`device unauthorized`): waited for, the same case held and launched again,
never a failed case; past the bound the run stops."""
import json, types

import pytest

from cryptobench.shared import paths
from cryptobench.shared.device import timeouts
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.device import adb as device_module
from fake_clock import FakeClock
from fake_phone import Phone
from test_device_benchmark_flow import OPTIONS, measured
from test_thermal_gate import GATE

UNAUTHORIZED = "adb: device unauthorized.\nThis adb server's $ADB_VENDOR_KEYS is not set\n"
SKIN = """Thermal Status: 0
HAL Ready: true
Current temperatures from HAL:
\tTemperature{mValue=30.0, mType=3, mName=VIRTUAL-SKIN, mStatus=0}
"""
# the transport dropped inside am instrument, which printed only the test's start
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


def lost_run(tmp_path, monkeypatch, polls, wait_minutes=1):
    FakeClock(monkeypatch)
    phone = LosingPhone(tmp_path, "b", polls, cases=("a", "b", "c", "d"))
    monkeypatch.setattr(timeouts, "run", phone.answer)
    monkeypatch.setattr("test_device_benchmark_flow.OPTIONS", types.SimpleNamespace(**{**vars(OPTIONS), "reconnect_wait_minutes": wait_minutes,
                                                                                         "reconnect_poll_seconds": 10}))
    return phone, measured(tmp_path, monkeypatch, {"thermalGate": GATE, "launchRetries": 1}, phone=phone)


def test_a_transport_lost_inside_am_instrument_is_waited_out_and_the_same_case_runs_again(tmp_path, monkeypatch, capsys):
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


def test_the_lost_attempt_is_kept_in_rejected_with_its_why(tmp_path, monkeypatch):
    _phone, (_p, _files, _problems, results) = lost_run(tmp_path, monkeypatch, polls=3)
    whys = [read_yaml(why) for why in paths.RunTree(results).rejected.rglob(paths.WHY)]
    assert [(w["case"], w["attempt"], w["findings"][0]["code"]) for w in whys] == [("b", 1, "device_lost")]


# adb shell exited 1 with no words of its own and the clocks read cut after 3 cores
PARTIAL = "cpu0 1 sched_pixel 300000 300000 2000000\ncpu1 1 sched_pixel 300000 300000 2000000\ncpu2 1"


def cut_device(tmp_path, monkeypatch, state):
    device = device_module.Device(tmp_path, False, False)
    answers = {"shell": types.SimpleNamespace(returncode=1, stdout=PARTIAL, stderr=""),
               "get-state": types.SimpleNamespace(returncode=0 if state else 1, stdout=state, stderr="")}
    monkeypatch.setattr(timeouts, "run", lambda _step, command, **_o: answers[command[1]])
    return device


def test_a_wordless_failure_with_the_device_gone_is_device_lost(tmp_path, monkeypatch):
    device = cut_device(tmp_path, monkeypatch, "")
    with pytest.raises(device_module.DeviceLost, match=r"^device_lost: adb get-state after adb shell: no answer$"):
        device.shell("for c in /sys/devices/system/cpu/cpu[0-9]*; do ...")
    with pytest.raises(device_module.DeviceLost):
        device.run("shell", "ls", check=False)


def test_a_wordless_failure_with_the_device_attached_stays_the_command_failure(tmp_path, monkeypatch):
    device = cut_device(tmp_path, monkeypatch, "device\n")
    with pytest.raises(device_module.DeviceError) as failed:
        device.shell("ls")
    assert type(failed.value) is device_module.DeviceError and str(failed.value).startswith("adb shell ls: cpu0 1")
    assert device.run("shell", "ls", check=False).returncode == 1


class CuttingPhone(Phone):
    """Cuts the transport inside the first process's clocks read: adb shell exits 1 with partial output and no words of its own."""

    def __init__(self, folder, polls, **options):
        super().__init__(folder, thermal=SKIN, **options)
        self.cut, self.polls, self.states = True, polls, []

    def shell(self, command):
        if self.cut and command.startswith("for c in /sys"):
            self.cut = False
            self.log.append("clocks cut")
            return device_module.Device.run(self, "shell", command).stdout
        return super().shell(command)

    def raw(self, *arguments):
        if arguments[0] == "get-state":
            self.states.append(self.polls)
            if self.polls == 0:
                return types.SimpleNamespace(returncode=0, stdout="device\n", stderr="")
            self.polls -= 1
            return types.SimpleNamespace(returncode=1, stdout="", stderr="")
        return types.SimpleNamespace(returncode=1, stdout=PARTIAL, stderr="")


def test_a_clocks_read_cut_mid_shell_is_waited_out_and_the_process_runs(tmp_path, monkeypatch, capsys):
    FakeClock(monkeypatch)
    phone = CuttingPhone(tmp_path, 2)
    monkeypatch.setattr("test_device_benchmark_flow.OPTIONS", types.SimpleNamespace(**{**vars(OPTIONS), "reconnect_wait_minutes": 1,
                                                                                         "reconnect_poll_seconds": 10}))
    _phone, _files, problems, results = measured(tmp_path, monkeypatch, {"thermalGate": GATE}, phone=phone)
    assert phone.states == [2, 1, 0] and problems == []
    assert phone.log.index("clocks cut") < phone.log.index("clocks")
    assert [s for s in phone.log if s.startswith("instrument ")] == ["instrument CryptoBenchmark a", "instrument CryptoBenchmark b"]
    assert [b["name"] for b in json.loads((results / "benchmark/benchmarkData.json").read_text())["benchmarks"]] == ["measure[a]", "measure[b]"]
    assert "device_lost: adb get-state after adb shell: no answer" in capsys.readouterr().out
