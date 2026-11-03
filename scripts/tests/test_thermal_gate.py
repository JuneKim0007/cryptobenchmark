"""run.thermalGate on a fake phone and a fake thermal reader: each case heats the device, each gate sleep cools it on a fake clock."""
import json, pathlib, sys, types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import pipeline  # noqa: E402
import thermal  # noqa: E402
import thermal_gate  # noqa: E402
from fake_phone import Phone  # noqa: E402
from test_device_benchmark_flow import measured  # noqa: E402
from test_scoped_flow import CASES, scoped  # noqa: E402

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


def test_a_case_waits_until_the_device_is_back_at_its_target(tmp_path, monkeypatch, capsys):
    heat = Heat(monkeypatch)
    _phone, _files, problems, results = measured(tmp_path, monkeypatch, {"isolation": "case", "thermalGate": GATE})
    out = capsys.readouterr().out
    assert "gate:      baseline 30.0 C, the hottest of BIG; a case starts at or below 33.0 C and status 0; MID absent, skipped" in out
    assert heat.slept == [5, 5] and problems == []
    assert gate_of(results, "a") == {"waitedSeconds": 0.0, "target": 33.0, "timedOut": False}
    assert gate_of(results, "b") == {"waitedSeconds": 10.0, "target": 33.0, "timedOut": False}
    assert json.loads((results / "benchmark/thermal.json").read_text())["gate"] == {"sensors": ["BIG", "MID"], "baseline": 30.0, "target": 33.0}
    assert "gate:      measure: 1 of 2 cases gated, 10 s waited, max 10 s, 0 timed out" in out


def test_past_the_timeout_the_case_starts_anyway_and_is_flagged(tmp_path, monkeypatch, capsys):
    heat = Heat(monkeypatch, cooling=0.0)
    _phone, _files, problems, results = measured(tmp_path, monkeypatch, {"isolation": "case", "thermalGate": GATE | {"timeoutSeconds": 12}})
    assert heat.slept == [5, 5, 2]
    assert gate_of(results, "b") == {"waitedSeconds": 12.0, "target": 33.0, "timedOut": True}
    assert problems == ["thermal_gate_timeout: b: measure: started after 12 s at 40.0 C, status 0, target 33.0 C"]
    assert "warning: thermal_gate_timeout: b" in capsys.readouterr().out


def test_no_configured_sensor_on_the_device_turns_the_gate_off_with_one_warning(tmp_path, monkeypatch, capsys):
    heat = Heat(monkeypatch, sensors=("skin",))
    _phone, _files, problems, results = measured(tmp_path, monkeypatch, {"isolation": "case", "thermalGate": GATE})
    out = capsys.readouterr().out
    assert out.count("warning: thermal_gate_off: none of BIG, MID among the device's sensors (skin); measuring without the gate") == 1
    assert heat.slept == [] and problems == [] and gate_of(results, "b") is None


def test_the_gate_is_off_by_default_and_when_disabled(tmp_path, monkeypatch, capsys):
    heat = Heat(monkeypatch)
    _phone, _files, _problems, results = measured(tmp_path, monkeypatch, {"isolation": "case"})
    _phone, _files, _problems, disabled = measured(tmp_path / "off", monkeypatch, {"isolation": "case", "thermalGate": GATE | {"enabled": False}})
    assert heat.slept == [] and "gate:" not in capsys.readouterr().out
    assert gate_of(results, "b") is None and gate_of(disabled, "b") is None


def test_the_warm_up_is_not_gated_and_the_baseline_is_read_after_it(tmp_path, monkeypatch, capsys):
    heat = Heat(monkeypatch)
    run = {"isolation": "case", "warmup": {"iterations": 10, "jobs": [{"name": "b*"}]}, "thermalGate": GATE}
    _phone, _files, _problems, results = measured(tmp_path, monkeypatch, run)
    out = capsys.readouterr().out
    assert out.index("warm-up:   1 cases x 10 samples") < out.index("gate:      baseline 40.0 C, the hottest of BIG")
    assert heat.slept == [5, 5] and heat.asleep_after == [2, 2]
    assert gate_of(results, "a")["waitedSeconds"] == 0.0 and gate_of(results, "b")["target"] == 43.0


def test_with_one_process_for_every_case_the_gate_holds_the_process_and_every_case_shares_it(tmp_path, monkeypatch, capsys):
    heat = Heat(monkeypatch)
    _phone, _files, _problems, results = measured(tmp_path, monkeypatch, {"isolation": "run", "processRepetitions": 2, "thermalGate": GATE})
    assert heat.slept == [5, 5]
    assert gate_of(results, "a", "benchmark/process-2") == gate_of(results, "b", "benchmark/process-2") == {
        "waitedSeconds": 10.0, "target": 33.0, "timedOut": False}
    assert "gate:      measure: 1 of 2 processes gated, 10 s waited" in capsys.readouterr().out


def test_the_before_after_run_is_gated_too(tmp_path, monkeypatch, capsys):
    heat = Heat(monkeypatch)
    _phone, _files, problems = scoped(tmp_path, monkeypatch, {"isolation": "case", "scopedRepetitions": 1, "thermalGate": GATE})
    assert heat.slept == [5, 5] * (len(CASES) - 1) and problems == []
    assert gate_of(tmp_path, CASES[-1], "scoped")["waitedSeconds"] == 10.0
    assert "gate:      measure: 3 of 4 cases gated, 30 s waited, max 10 s, 0 timed out" in capsys.readouterr().out


def test_a_host_run_measures_without_the_gate_and_says_so_once(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(pipeline.gradle_runner, "run", lambda *_arguments, **_options: [])
    document = {"run": {"thermalGate": GATE}}
    pipeline.host_cases(types.SimpleNamespace(stacktrace=False, stream=False), document, "c", "t", "e", tmp_path, tmp_path, {})
    assert capsys.readouterr().out.count("warning: thermal_gate_off: run.thermalGate: only a --device run") == 1
