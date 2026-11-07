"""run.thermalGate on a fake phone and a fake thermal reader: each case heats the device, each gate sleep cools it on a fake clock."""
import json, pathlib, sys, types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from stages import benchmark  # noqa: E402
from device import thermal  # noqa: E402
from session import thermal_gate  # noqa: E402
from fake_phone import Phone  # noqa: E402
from test_device_benchmark_flow import RUN, measured  # noqa: E402

GATE = {"enabled": True, "sensors": ["BIG", "MID"], "marginCelsius": 3.0, "pollSeconds": 5, "timeoutSeconds": 300}


class Heat:
    """BIG starts at 30 C, every measuring process adds `rise`, every second of gate sleep takes `cooling` off; status stays 0."""

    def __init__(self, monkeypatch, rise=10.0, cooling=1.0, sensors=("BIG", "skin")):
        self.celsius, self.rise, self.cooling, self.sensors, self.now, self.slept, self.processes = 30.0, rise, cooling, sensors, 0.0, [], []
        monkeypatch.setattr(thermal_gate, "thermal", types.SimpleNamespace(read=self.read))
        monkeypatch.setattr(thermal_gate, "time", types.SimpleNamespace(monotonic=lambda: self.now, sleep=self.sleep))
        original = Phone.instrument

        def instrument(phone, test_class, *arguments, **options):
            if "log" not in arguments:
                self.celsius += self.rise
                self.processes.append(test_class)
            return original(phone, test_class, *arguments, **options)
        monkeypatch.setattr(Phone, "instrument", instrument)

    def read(self, _device):
        return thermal.Reading({name: self.celsius if name == "BIG" else 99.0 for name in self.sensors}, 0, "hal")

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.asleep_after = getattr(self, "asleep_after", []) + [len(self.processes)]
        self.now += seconds
        self.celsius -= seconds * self.cooling


def gate_of(results, case, folder="benchmark"):
    return json.loads((results / folder / "thermal.json").read_text())["cases"][case].get("gate")


def test_a_case_waits_until_the_device_is_back_at_its_target(tmp_path, monkeypatch):
    heat = Heat(monkeypatch)
    _phone, _files, problems, results = measured(tmp_path, monkeypatch, {"isolation": "case", "thermalGate": GATE})
    assert heat.slept == [5, 5] and problems == []
    assert gate_of(results, "a") == {"waitedSeconds": 0.0, "target": 33.0, "timedOut": False}
    assert gate_of(results, "b") == {"waitedSeconds": 10.0, "target": 33.0, "timedOut": False}
    assert json.loads((results / "benchmark/thermal.json").read_text())["gate"] == {"sensors": ["BIG", "MID"], "baseline": 30.0, "target": 33.0}


def test_past_the_timeout_the_case_starts_anyway_and_is_flagged(tmp_path, monkeypatch):
    heat = Heat(monkeypatch, cooling=0.0)
    _phone, _files, problems, results = measured(tmp_path, monkeypatch, {"isolation": "case", "thermalGate": GATE | {"timeoutSeconds": 12}})
    assert heat.slept == [5, 5, 2]
    assert gate_of(results, "b") == {"waitedSeconds": 12.0, "target": 33.0, "timedOut": True}
    assert [line.split(": ")[:2] for line in problems] == [["thermal_gate_timeout", "b"]]


def test_no_configured_sensor_on_the_device_turns_the_gate_off_with_one_warning(tmp_path, monkeypatch, capsys):
    heat = Heat(monkeypatch, sensors=("skin",))
    _phone, _files, problems, results = measured(tmp_path, monkeypatch, {"isolation": "case", "thermalGate": GATE})
    out = capsys.readouterr().out
    assert out.count("thermal_gate_off") == 1
    assert heat.slept == [] and problems == [] and gate_of(results, "b") is None


def test_the_gate_is_off_by_default_and_when_disabled(tmp_path, monkeypatch):
    heat = Heat(monkeypatch)
    _phone, _files, _problems, results = measured(tmp_path, monkeypatch, {"isolation": "case"})
    _phone, _files, _problems, disabled = measured(tmp_path / "off", monkeypatch, {"isolation": "case", "thermalGate": GATE | {"enabled": False}})
    assert heat.slept == []
    assert gate_of(results, "b") is None and gate_of(disabled, "b") is None


def test_the_baseline_is_read_idle_before_the_warm_up_and_the_warm_up_is_not_gated(tmp_path, monkeypatch):
    heat = Heat(monkeypatch)
    run = {"isolation": "case", "warmup": {"iterations": 10, "jobs": [{"provider": "P", "type": "T", "name": "b"}]}, "thermalGate": GATE}
    _phone, _files, _problems, results = measured(tmp_path, monkeypatch, run)
    assert heat.slept == [5, 5, 5, 5] and heat.asleep_after == [1, 1, 2, 2]
    assert gate_of(results, "a")["waitedSeconds"] == 10.0 and gate_of(results, "b")["target"] == 33.0


def test_with_one_process_for_every_case_the_gate_holds_the_process_and_every_case_shares_it(tmp_path, monkeypatch):
    heat = Heat(monkeypatch)
    _phone, _files, _problems, results = measured(tmp_path, monkeypatch, {"isolation": "run", "processRepetitions": 2, "thermalGate": GATE})
    assert heat.slept == [5, 5]
    assert gate_of(results, "a", "benchmark/process-2") == gate_of(results, "b", "benchmark/process-2") == {
        "waitedSeconds": 10.0, "target": 33.0, "timedOut": False}


def test_a_host_run_measures_without_the_gate_and_says_so_once(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(benchmark.gradle_runner, "run", lambda *_arguments, **_options: [])
    document = {"run": {**RUN, "thermalGate": GATE}}
    benchmark.host_cases(types.SimpleNamespace(stacktrace=False, stream=False), document, "c", "t", "e", tmp_path, tmp_path, {})
    assert capsys.readouterr().out.count("thermal_gate_off") == 1


def test_a_delta_session_gates_to_the_stored_baseline_not_a_new_reading(tmp_path, monkeypatch):
    heat = Heat(monkeypatch)
    monkeypatch.setenv(thermal_gate.STORED_BASELINE, "25.0")
    _phone, _files, _problems, results = measured(tmp_path, monkeypatch, {"isolation": "case", "thermalGate": GATE})
    assert gate_of(results, "a")["target"] == 28.0 and heat.slept
