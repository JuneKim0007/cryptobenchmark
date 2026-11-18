"""Py-P4 (decision 39.4): the thermal gate's hold returns False on an unreadable temperature; the case launch skips the case, the warm-up and the
energy dry pass are skipped."""
from cryptobench.stages.measurement import benchmark
from cryptobench.stages.measurement.session import dynamic_temperature, warmup
from test_device_benchmark_flow import measured
from test_thermal_gate import CASE, Heat


def blind_for(monkeypatch, heat, label):
    """The temperature is unreadable while the gate holds `label`, readable everywhere else."""
    real, held = dynamic_temperature.DynamicTemperature.hold, []

    def hold(self, case):
        if case != label:
            return real(self, case)
        heat.unreadable = set(range(heat.reads + 1, heat.reads + 100))
        try:
            held.append(real(self, case))
        finally:
            heat.unreadable = set()
        return held[-1]
    monkeypatch.setattr(dynamic_temperature.DynamicTemperature, "hold", hold)
    return held


def test_an_unreadable_temperature_before_the_warm_up_skips_it(tmp_path, monkeypatch):
    heat = Heat(monkeypatch)
    held = blind_for(monkeypatch, heat, "warm-up")
    phone, _files, problems, _results = measured(tmp_path, monkeypatch, CASE | {"warmup": {"iterations": 5, "jobs": []}})
    assert held == [False]
    assert not [a for a in phone.arguments if warmup.WARMUP_PASS in a]
    assert problems[0] == "temperature_unreadable: warm-up: thermal_unavailable: fake"
    assert [s for s in phone.log if s.startswith("instrument ")][-2:] == ["instrument CryptoBenchmark a", "instrument CryptoBenchmark b"]


def test_an_unreadable_temperature_before_the_energy_dry_pass_skips_it(tmp_path, monkeypatch):
    heat = Heat(monkeypatch)
    held = blind_for(monkeypatch, heat, "energy dry pass")
    ran = []
    monkeypatch.setattr(benchmark.EnergySession, "dry_pass", lambda *_arguments, **_options: ran.append("dry pass"))
    _phone, _files, problems, _results = measured(tmp_path, monkeypatch, CASE | {"harness": {"energy": {"capture": "dry"}}})
    assert held == [False] and ran == []
    assert problems[0] == "temperature_unreadable: energy dry pass: thermal_unavailable: fake"
