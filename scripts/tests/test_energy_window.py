"""pipeline.measure_on_device around a source: the window spans the device run, joules comes after it."""
import contextlib, pathlib, sys, types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import pipeline  # noqa: E402

OPTIONS = types.SimpleNamespace(stream=False, suppress_errors="", stacktrace=False)


class Recorder:

    def __init__(self, failing=()):
        self.calls, self.failing = [], failing

    def window(self, _folder):
        @contextlib.contextmanager
        def around():
            self.calls.append("open")
            yield
            self.calls.append("close")
        return around()

    def joules(self, *_paths):
        self.calls.append("joules")
        if "joules" in self.failing:
            raise pipeline.energy_stage.EnergyError("tools/energy/energy.py: boom")

    def measure(self, *_arguments):
        self.calls.append("measure")
        return []

    def pull_traces(self, _traces):
        self.calls.append("pull")
        if "pull" in self.failing:
            raise pipeline.DeviceError("adb pull x: device offline")
        return 0

    def dry_pass(self, *_arguments):
        self.calls.append("dry")


def run(tmp_path, monkeypatch, captures, failing=(), problems=None, converted=None):
    monkeypatch.setattr(pipeline.clocks, "read", lambda _device: {})
    monkeypatch.setattr(pipeline.clocks, "write", lambda *_arguments: None)
    monkeypatch.setattr(pipeline.gradle_runner, "run", lambda *arguments, **_options: (converted if converted is not None else []).append(arguments[1]))
    recorder = Recorder(failing)
    pipeline.measure_on_device(recorder, recorder, recorder, OPTIONS, captures, [], tmp_path, tmp_path, tmp_path,
                               [] if problems is None else problems)
    return recorder.calls


def test_measured_and_dry_run_inside_the_window_and_joules_after_it(tmp_path, monkeypatch):
    assert run(tmp_path, monkeypatch, {"measured", "dry"}) == ["open", "measure", "pull", "dry", "close", "joules"]


def test_no_capture_opens_no_window_whatever_the_source(tmp_path, monkeypatch):
    assert run(tmp_path, monkeypatch, {"none"}) == ["measure"]


def test_a_failed_energy_step_is_one_recorded_line_and_timing_is_still_converted(tmp_path, monkeypatch, capsys):
    problems, converted = [], []
    calls = run(tmp_path, monkeypatch, {"measured"}, failing=("pull", "joules"), problems=problems, converted=converted)
    assert calls == ["open", "measure", "pull", "close", "joules"]
    assert problems == ["energy_failed: adb pull x: device offline", "energy_failed: tools/energy/energy.py: boom"]
    assert capsys.readouterr().err.count("error: energy_failed: ") == 2
    assert len(converted) == 1 and "energy.json" not in converted[0]
