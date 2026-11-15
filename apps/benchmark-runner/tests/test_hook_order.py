"""The production order of a device session's hooks, outermost first, per pass, as measuring.timed_hooks and benchmark build it."""
from cryptobench.stages.measurement.session import measure as measure_session
from stages import benchmark
from cryptobench.stages.measurement.session import thermal_hook
from test_device_benchmark_flow import MEASURED, measured
from test_thermal_gate import CASE, Heat

TIMED = ["Cooldown", "Clocks", "Thermal"]


def hook_orders(tmp_path, monkeypatch, run):
    seen = []
    real = measure_session.run_session

    def recorded(device, plan, repetitions, isolation, hooks, folder, problems):
        seen.append((plan, [type(h).__name__ for h in hooks], hooks))
        return real(device, plan, repetitions, isolation, hooks, folder, problems)
    monkeypatch.setattr(measure_session, "run_session", recorded)
    measured(tmp_path, monkeypatch, run)
    return seen


def test_a_timed_session_without_energy_runs_cooldown_clocks_thermal(tmp_path, monkeypatch):
    assert [names for _p, names, _h in hook_orders(tmp_path, monkeypatch, {"isolation": "case"})] == [TIMED]


def test_isolation_run_keeps_the_same_order(tmp_path, monkeypatch):
    assert [names for _p, names, _h in hook_orders(tmp_path, monkeypatch, {"isolation": "run"})] == [TIMED]


def test_measured_energy_puts_the_capture_outermost_in_its_own_pass_only(tmp_path, monkeypatch):
    orders = [names for _p, names, _h in hook_orders(tmp_path, monkeypatch, MEASURED)]
    assert orders == [["EnergyCapture", *TIMED], TIMED]


def test_a_dry_capture_alone_has_only_the_energy_hook(tmp_path, monkeypatch):
    monkeypatch.setattr(benchmark.EnergySession, "dry_pass", lambda *_arguments: None)
    orders = [names for _p, names, _h in hook_orders(tmp_path, monkeypatch, {"harness": {"energy": {"capture": "dry"}}})]
    assert orders == [["EnergyCapture"]]


def test_a_gated_run_has_the_same_order_and_no_hook_holds_the_gate_only_its_history(tmp_path, monkeypatch):
    Heat(monkeypatch)
    (plan, names, hooks), = hook_orders(tmp_path, monkeypatch, CASE)
    assert names == TIMED
    thermal = hooks[2]
    assert isinstance(thermal, thermal_hook.Thermal) and thermal.history is plan.gate.history
    assert not any(plan.gate in vars(hook).values() for hook in hooks)
