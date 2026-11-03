"""The energy hook around a device process: the window spans the device run, joules comes after it, a failed energy step costs only energy."""
import pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import energy_stage, measure_session, session_hooks  # noqa: E402
from device import DeviceError  # noqa: E402
from fake_phone import Energy, Phone  # noqa: E402


class Session:

    def __init__(self, phone, failing):
        self.phone, self.failing = phone, failing

    def pull_traces(self, _traces):
        self.phone.log.append("pull traces")
        if "pull" in self.failing:
            raise DeviceError("adb pull x: device offline")
        return 0


class FailingEnergy(Energy):

    def joules(self, *_paths):
        super().joules()
        raise energy_stage.EnergyError("tools/energy/energy.py: boom")


def run(tmp_path, captures, failing=(), problems=None, timed=True):
    phone = Phone(tmp_path, cases=("a",))
    source = (FailingEnergy if "joules" in failing else Energy)(phone)
    dry = lambda _into, guarded: phone.log.append(f"dry guarded={guarded}")
    hook = session_hooks.EnergyCapture(source, Session(phone, failing), captures, tmp_path, tmp_path, [] if problems is None else problems, dry, timed)
    plan = measure_session.Plan("CryptoBenchmark", (), cases=("a",), timed=timed)
    measure_session.run_session(phone, plan, 1, "case", [hook], lambda _r: tmp_path / "b", [] if problems is None else problems)
    return [line for line in phone.log if line in ("window open", "window close", "joules", "pull traces") or line.startswith(("dry", "instrument"))]


def test_measured_and_dry_run_inside_the_window_and_joules_after_it(tmp_path):
    assert run(tmp_path, {"measured", "dry"}) == ["window open", "instrument CryptoBenchmark a", "pull traces", "dry guarded=True",
                                                  "window close", "joules"]


def test_a_dry_only_run_measures_nothing_timed_and_its_dry_pass_is_the_measurement(tmp_path):
    assert run(tmp_path, {"dry"}, timed=False) == ["window open", "dry guarded=False", "window close", "joules"]


def test_a_failed_energy_step_is_one_recorded_line(tmp_path, capsys):
    problems = []
    calls = run(tmp_path, {"measured"}, failing=("pull", "joules"), problems=problems)
    assert calls == ["window open", "instrument CryptoBenchmark a", "pull traces", "window close", "joules"]
    assert problems == ["energy_failed: adb pull x: device offline", "energy_failed: tools/energy/energy.py: boom"]
    assert capsys.readouterr().err.count("error: energy_failed: ") == 2
