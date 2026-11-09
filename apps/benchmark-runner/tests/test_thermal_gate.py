"""run.thermalGate on a fake phone: a fake temperature that each launch raises and each second of waiting lowers."""
import json, types

import pytest

from stages import benchmark  # noqa: E402
from device import thermal  # noqa: E402
from device.adb import DeviceError  # noqa: E402
from session import dynamic_temperature, thermal_hook  # noqa: E402
from fake_phone import Phone  # noqa: E402
from test_device_benchmark_flow import RUN, measured  # noqa: E402

MARGIN = {"dynamic": True, "initialCelsius": 0.25, "backoffFactor": 2.0, "maximumCelsius": 3.0, "cleanRunsToRecover": 10, "recoveryCelsius": 0.05}
GATE = {"temperatureKeptCelsius": 36.0, "cooldownMinutes": 3, "pollMinutes": 1, "pollTerminateMinutes": 30, "discardLimit": 5,
        "onDiscardLimit": "nextCase", "readRetries": 2, "readRetrySeconds": 1, "startMargin": MARGIN}
CASE = {"isolation": "case", "thermalGate": GATE}


class Heat:
    """Skin starts at `start`, each measuring launch adds `rise`, each second asleep takes `cooling` off."""

    def __init__(self, monkeypatch, start=30.0, rise=0.0, cooling=0.05, available=True, reason="ok", unreadable=()):
        self.celsius, self.rise, self.cooling, self.now, self.slept, self.launches, self.reads = start, rise, cooling, 0.0, [], [], 0
        self.unreadable = set(unreadable)
        fake = types.SimpleNamespace(read=self.read, poll=self.read, capability=lambda _device: thermal.Capability(available, reason, ("skin",)))
        monkeypatch.setattr(dynamic_temperature, "thermal", fake)
        monkeypatch.setattr(thermal_hook, "thermal", fake)
        monkeypatch.setattr(dynamic_temperature, "time", types.SimpleNamespace(monotonic=lambda: self.now, sleep=self.sleep))
        original = Phone.instrument

        def instrument(phone, test_class, *arguments, **options):
            if "log" not in arguments:
                self.celsius += self.rise
                self.launches.append(arguments)
            return original(phone, test_class, *arguments, **options)
        monkeypatch.setattr(Phone, "instrument", instrument)

    def read(self, _device):
        self.reads += 1
        if self.reads in self.unreadable:
            return thermal.Reading(None, None, None, "thermal_unavailable: fake")
        return thermal.Reading({"skin": self.celsius}, 0, "hal", types={"skin": 3})

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds
        self.celsius -= seconds * self.cooling


def gate_of(results, case):
    return json.loads((results / "benchmark/thermal.json").read_text())["cases"][case].get("gate")


def test_not_set_says_so_and_never_waits(tmp_path, monkeypatch, capsys):
    heat = Heat(monkeypatch, start=50.0)
    measured(tmp_path, monkeypatch, {"isolation": "case"})
    assert heat.slept == [] and capsys.readouterr().out.count("TEMPERATURE GATE OFF") == 1


def test_a_device_that_cannot_report_runs_with_one_visible_line(tmp_path, monkeypatch, capsys):
    heat = Heat(monkeypatch, start=50.0, available=False, reason="simulated_device")
    _phone, _files, problems, _results = measured(tmp_path, monkeypatch, CASE)
    assert heat.slept == [] and len(heat.launches) == 2
    assert capsys.readouterr().out.count("TEMPERATURE SET BUT DEVICE CAN'T POLL: simulated_device") == 1
    assert problems == ["TEMPERATURE SET BUT DEVICE CAN'T POLL: simulated_device; running without it"]


def test_a_cool_phone_starts_at_once(tmp_path, monkeypatch, capsys):
    heat = Heat(monkeypatch)
    _phone, _files, problems, results = measured(tmp_path, monkeypatch, CASE)
    assert heat.slept == [] and problems == []
    assert gate_of(results, "a") == {"waitedSeconds": 0.0, "target": 35.75, "discards": 0}
    assert "TEMPERATURE GATE SET: kept 36.0 C on skin" in capsys.readouterr().out


def test_a_hot_start_waits_three_minutes_then_polls_each_minute(tmp_path, monkeypatch, capsys):
    heat = Heat(monkeypatch, start=45.0, cooling=0.05)  # 180 s takes it to 36.0, two polls at 60 s reach 35.75 or below
    _phone, _files, problems, results = measured(tmp_path, monkeypatch, CASE)
    assert heat.slept[0] == 180 and set(heat.slept[1:]) == {60} and problems == []
    assert gate_of(results, "a")["waitedSeconds"] == sum(heat.slept)
    assert "=> waiting 3 minutes to cool down, then polling every 1 min" in capsys.readouterr().out


def test_polling_past_the_limit_stops_the_benchmark(tmp_path, monkeypatch):
    Heat(monkeypatch, start=50.0, cooling=0.0)
    with pytest.raises(dynamic_temperature.Terminated, match="temperature_gate_timeout"):
        measured(tmp_path, monkeypatch, CASE)


def test_a_run_ending_hot_is_discarded_measured_again_and_widens_the_margin(tmp_path, monkeypatch, capsys):
    heat = Heat(monkeypatch, start=35.7, rise=0.4, cooling=0.05)
    _phone, _files, problems, results = measured(tmp_path, monkeypatch, CASE)
    assert len(heat.launches) > 2 and problems == []
    out = capsys.readouterr().out
    assert "discarded, ended at 36.1 C" in out and "start margin now 0.50 C" in out
    assert gate_of(results, "a")["discards"] == 1 and gate_of(results, "a")["target"] == 35.5


def test_dynamic_false_keeps_the_margin_after_a_discard(tmp_path, monkeypatch):
    gate = GATE | {"startMargin": MARGIN | {"dynamic": False}}
    Heat(monkeypatch, start=35.7, rise=0.4, cooling=0.05)
    _phone, _files, _problems, results = measured(tmp_path, monkeypatch, {"isolation": "case", "thermalGate": gate})
    assert gate_of(results, "a")["target"] == 35.75 and gate_of(results, "b")["target"] == 35.75


def test_a_run_that_keeps_ending_hot_stops_at_the_limit_and_the_next_case_goes_on(tmp_path, monkeypatch, capsys):
    gate = GATE | {"discardLimit": 2}
    heat = Heat(monkeypatch, start=30.0, rise=10.0, cooling=0.05)
    with pytest.raises(DeviceError):  # every case ends over the limit here, so no case is left measured
        measured(tmp_path, monkeypatch, {"isolation": "case", "thermalGate": gate})
    assert len(heat.launches) == 4 and capsys.readouterr().out.count("temperature_discard_limit") >= 2


def test_on_discard_limit_stop_ends_the_benchmark(tmp_path, monkeypatch):
    gate = GATE | {"discardLimit": 1, "onDiscardLimit": "stop"}
    Heat(monkeypatch, start=30.0, rise=10.0, cooling=1.0)
    with pytest.raises(dynamic_temperature.Terminated, match="temperature_discard_limit"):
        measured(tmp_path, monkeypatch, {"isolation": "case", "thermalGate": gate})


def test_an_unreadable_start_retries_then_moves_to_the_next_case(tmp_path, monkeypatch):
    heat = Heat(monkeypatch, unreadable={2, 3, 4})  # read 1 is the process start
    _phone, _files, problems, _results = measured(tmp_path, monkeypatch, CASE)
    assert heat.slept == [1, 1] and len(heat.launches) == 1
    assert [p.split(":")[0] for p in problems].count("temperature_unreadable") == 1
    assert any(p.startswith("case_failed: a: temperature_unreadable") for p in problems)


def test_a_failed_reading_never_counts_as_a_pass(tmp_path, monkeypatch):
    heat = Heat(monkeypatch, start=45.0, cooling=0.05, unreadable={3, 4, 5})
    measured(tmp_path, monkeypatch, CASE)
    assert heat.slept[0] == 180 and sum(heat.slept) > 180


def test_a_host_run_says_it_cannot_poll_once(tmp_path, monkeypatch, capsys):
    document = {"run": {**RUN, "thermalGate": GATE}, "bundledProviders": []}
    problems = []
    monkeypatch.setattr(benchmark.gradle_runner, "run", lambda *_a, **_k: [])
    monkeypatch.setattr(benchmark, "record", lambda *_a, **_k: None)
    benchmark.host_cases(types.SimpleNamespace(stacktrace=False, stream=False), document, "c", "t", "e", tmp_path / "b", tmp_path / "p", {}, problems)
    assert capsys.readouterr().out.count("TEMPERATURE SET BUT DEVICE CAN'T POLL: host_runtime") == 1


def test_the_skin_reading_ignores_the_cached_section_and_other_types():
    live = thermal.Reading({"skin": 36.2, "BIG": 50.0}, 0, "hal", types={"skin": 3, "BIG": 0})
    assert live.skin == ("skin", 36.2) and thermal.Reading({"skin": 36.2}, 0, "cached", types={"skin": 3}).skin is None


@pytest.mark.parametrize("text, reason", [
    ("", "no_thermal_service"), ("Can't find service: thermalservice", "no_thermal_service"),
    ("HAL Ready: false\n", "hal_not_ready"), ("Thermal Status: 0\n", "no_temperatures"),
    ("Cached temperatures:\n\tTemperature{mValue=30.0, mType=3, mName=skin, mStatus=0}\n", "cached_only"),
    ("Current temperatures from HAL:\n\tTemperature{mValue=30.0, mType=0, mName=BIG, mStatus=0}\n", "no_skin_sensor"),
    ("Current temperatures from HAL:\n\tTemperature{mValue=30.0, mType=3, mName=skin, mStatus=0}\n", "ok"),
])
def test_every_availability_outcome(text, reason):
    assert thermal.judged(text)[0] == reason


def test_a_simulated_device_cannot_poll():
    device = types.SimpleNamespace(shell=lambda command: "ranchu\n" if command.startswith("getprop") else "")
    assert thermal.capability(device) == thermal.Capability(False, "simulated_device")


def test_a_reading_from_an_earlier_hold_is_never_a_later_runs_start(monkeypatch):
    heat = Heat(monkeypatch)
    session = dynamic_temperature.Gate(None, dynamic_temperature.Settings.of(GATE), ("skin",), []).session("timing")
    assert session.hold("warm-up")
    heat.celsius = 45.0
    assert session.hold("first case")
    assert session.take_start() is None


def test_the_wait_line_names_the_configured_polling_interval(monkeypatch, capsys):
    heat = Heat(monkeypatch, start=45.0)
    session = dynamic_temperature.Gate(None, dynamic_temperature.Settings.of({**GATE, "pollMinutes": 2}), ("skin",), []).session("timing")
    assert session.hold("case") and heat.slept[0] == 180
    assert "then polling every 2 min" in capsys.readouterr().out


def test_each_process_reports_only_its_own_waits_and_discards(monkeypatch):
    heat = Heat(monkeypatch)
    session = dynamic_temperature.Gate(None, dynamic_temperature.Settings.of(GATE), ("skin",), []).session("timing")
    assert session.hold("c")
    heat.celsius = 40.0
    assert session.verdict("c") == "hot"
    heat.celsius = 45.0
    assert session.hold("c") and heat.slept == [180, 60]
    assert session.verdict("c") == "clean"
    assert session.records() == {"c": {"waitedSeconds": 240.0, "target": 35.5, "discards": 1}}
    assert session.hold("c") and session.verdict("c") == "clean"
    assert session.records() == {"c": {"waitedSeconds": 0.0, "target": 35.5, "discards": 0}}
