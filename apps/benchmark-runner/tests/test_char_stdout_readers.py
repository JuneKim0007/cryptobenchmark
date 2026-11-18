"""Characterization (Py-P12): the orchestrator's Worker.outcome and perf-repair's pipeline readers over transcripts the runner printed under the
fakes, stdout and stderr in one stream as a worker's log and perf-repair's pipe receive them."""
import collections, io, pathlib, signal, sys, types

import pytest

import failure
import pipeline
from cryptobench.pipeline.orchestrator.worker import Outcome, Worker
from cryptobench.shared.errors.halt import Halt
from cryptobench.shared.errors.failures import EnergyError
from fake_phone import Energy
from perfrepair.data_handler.outbound import benchmark_runner
from perfrepair.device.delta_estimate import _whole_run_took
from test_char_publish_routes import routed
from test_device_benchmark_flow import MEASURED
from test_rerun_safety import stopped_at


class Merged(io.StringIO):
    def reconfigure(self, **_options):
        pass


def transcript(rerun, monkeypatch, **flags):
    """What the entry point prints for one run, in order, and its exit code as `python pipeline.py` would end."""
    out = Merged()
    monkeypatch.setattr(sys, "stdout", out)
    monkeypatch.setattr(sys, "stderr", out)
    code = 0
    try:
        try:
            with failure.reported():
                rerun(**flags)
        except Exception as error:
            failure.fail(pipeline.failure_line(error))
    except SystemExit as stop:
        code = stop.code
    except KeyboardInterrupt:
        code = -signal.SIGTERM
    monkeypatch.undo()
    return out.getvalue().splitlines(), code


def outcome(tmp_path, lines, code, stopped=False):
    log = tmp_path / "worker.log"
    log.write_text("".join(f"{line}\n" for line in lines))
    worker = Worker(["pipeline.py"], None, log)
    worker.process, worker.stopped = types.SimpleNamespace(returncode=code), stopped
    return worker.outcome()


def streamed(lines):
    process = types.SimpleNamespace(stdout=iter(f"{line}\n" for line in lines))
    return benchmark_runner._stream(process, io.StringIO(), collections.deque(maxlen=40), None)


def failed_line(lines, code):
    with pytest.raises(Halt) as halted:
        benchmark_runner._failed("device", code, lines[-40:], "ref", None)
    return str(halted.value).split("; full log ")[0]


def energy_refused(monkeypatch):
    def refused(_self, _folder):
        raise EnergyError("manafa_cannot_start: no session")
    monkeypatch.setattr(Energy, "window", refused)


def test_today_a_finished_measured_run(tmp_path, monkeypatch):
    rerun = routed(tmp_path, monkeypatch)
    lines, code = transcript(rerun, monkeypatch)
    assert code == 0 and outcome(tmp_path, lines, code) == Outcome("finished", None, str(rerun.device))
    assert streamed(lines) == rerun.device / "manifest.yaml"
    assert len(_whole_run_took(lines)) == 1


def test_interop_gives_the_worker_its_results_line(tmp_path, monkeypatch):
    rerun = routed(tmp_path, monkeypatch)
    lines, code = transcript(rerun, monkeypatch, interop=str(rerun.plan))
    assert code == 0 and outcome(tmp_path, lines, code).results == str(rerun.device)
    assert streamed(lines) == rerun.device / "manifest.yaml"


def test_today_a_check_with_failures_reads_its_coded_line(tmp_path, monkeypatch):
    rerun = routed(tmp_path, monkeypatch)
    monkeypatch.setattr("test_char_publish_routes.CHECKED", "summary: {cases: 1, outcomes: {fail: 1}, oracles: {}}\ncases: [{id: a, outcome: fail, reason: r}]\n")
    lines, code = transcript(rerun, monkeypatch, check=True)
    assert code == 1 and lines[-1].startswith("error: check_failed: 1 cases failed or errored, see ")
    found = outcome(tmp_path, lines, code)
    assert found.state == "failed" and found.code == "check_failed" and found.results == str(rerun.device)
    assert failed_line(lines, code).startswith("pipeline_failed: pipeline exited 1 (device); error: check_failed: 1 cases failed")
    assert streamed(lines) == rerun.device / "manifest.yaml"


def test_an_energy_step_the_run_survived_prints_a_warning_and_finishes(tmp_path, monkeypatch):
    energy_refused(monkeypatch)
    rerun = routed(tmp_path, monkeypatch)
    lines, code = transcript(rerun, monkeypatch, run=MEASURED)
    assert code == 0 and "warning: energy_failed: manafa_cannot_start: no session" in lines
    assert not [line for line in lines if line.startswith("error")]
    assert outcome(tmp_path, lines, code) == Outcome("finished", None, str(rerun.device))


def test_a_run_killed_after_a_survived_energy_step_is_not_blamed_on_it(tmp_path, monkeypatch):
    energy_refused(monkeypatch)
    rerun = routed(tmp_path, monkeypatch)
    lines, _code = transcript(rerun, monkeypatch, run=MEASURED)
    found = outcome(tmp_path, lines[:-3], -signal.SIGKILL)
    assert found.state == "failed" and found.line == f"subprocess_failed: pipeline.py exited {-signal.SIGKILL}"
    assert "energy_failed" not in failed_line(lines[:-3], -signal.SIGKILL)


def test_today_a_stopped_run_prints_no_error_line_and_its_last_wrote_line_is_the_partial_manifest(tmp_path, monkeypatch):
    rerun = routed(tmp_path, monkeypatch)
    stopped_at(rerun.phone, monkeypatch, "b", KeyboardInterrupt())
    lines, code = transcript(rerun, monkeypatch)
    assert not [line for line in lines if line.startswith("error")]
    assert outcome(tmp_path, lines, code, stopped=True) == Outcome("stopped", f"subprocess_failed: pipeline.py exited {code}", str(rerun.device))
    assert streamed(lines) == rerun.device / "manifest.yaml"


def test_today_a_device_error_is_the_last_error_line_for_both_readers(tmp_path, monkeypatch):
    from cryptobench.shared.device.adb import DeviceError
    rerun = routed(tmp_path, monkeypatch)
    stopped_at(rerun.phone, monkeypatch, "b", DeviceError("adb shell: closed by the test"))
    lines, code = transcript(rerun, monkeypatch)
    assert code == 1 and lines[-1] == "error: adb shell: closed by the test"
    assert outcome(tmp_path, lines, code).line == "adb shell: closed by the test"
    assert failed_line(lines, code).endswith("; error: adb shell: closed by the test")
    assert streamed(lines) == rerun.device / "manifest.yaml" and pathlib.Path(streamed(lines)).is_file()
