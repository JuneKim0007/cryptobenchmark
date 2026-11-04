import json
import shutil
import time
from pathlib import Path

import pytest

from helpers import captured_events

from perfrepair import run_dir as rd
from perfrepair.config.load import load
from perfrepair.config.stops import install_stops
from perfrepair.stop import Halt
from perfrepair.data_handler.outbound import benchmark_runner
from perfrepair.data_handler.outbound import BenchmarkRunError, benchmark_root, run_pipeline

FAKE = Path(__file__).parent / "fixtures" / "outbound" / "fake_pipeline.py"

@pytest.fixture
def bench_root(tmp_path):
    root = tmp_path / "bench"
    (root / "apps/benchmark-runner").mkdir(parents=True)
    shutil.copy(FAKE, root / "apps/benchmark-runner" / "pipeline.py")
    return root


@pytest.mark.parametrize("stage,flag", [("configure", None), ("bench", "--bench"), ("device", "--device")])
def test_runner_passes_stage_and_returns_manifest(bench_root, tmp_path, stage, flag):
    config = tmp_path / "c.yaml"
    seen = []
    manifest = run_pipeline(config, tmp_path / "benchmark", stage, bench_root, echo=seen.append, device=tmp_path / "d")
    assert manifest == (tmp_path / "benchmark" / "fake-device" / "manifest.yaml").resolve()
    argv = json.loads((tmp_path / "benchmark" / "argv.json").read_text())["argv"]
    assert argv[argv.index("--config") + 1] == str(config.resolve())
    assert ("--bench" in argv, "--device" in argv) == (flag == "--bench", flag == "--device")
    logs = list((tmp_path / "d" / rd.PIPELINE_LOGS).iterdir())
    assert seen[0] == "line 0" and len(logs) == 1 and logs[0].read_text().startswith(f"# {stage}\n$ ")
    assert not (tmp_path / "benchmark" / "pipeline.log").exists()


def test_a_run_keeps_every_pipeline_call_in_its_own_transcript(bench_root, tmp_path, monkeypatch):
    config = tmp_path / "c.yaml"
    monkeypatch.setattr(benchmark_runner, "run_id", lambda: "r1")
    run_pipeline(config, tmp_path / "benchmark", "configure", bench_root, echo=None, device=tmp_path / "d")
    first = (tmp_path / "d" / rd.PIPELINE_LOGS / "r1.log").read_text().count("\n")
    monkeypatch.setenv("FAKE_EXIT", "3")
    with pytest.raises(Halt, match=rf"full log {tmp_path / 'd' / rd.PIPELINE_LOGS / 'r1.log'}:{first + 1};"):
        run_pipeline(config, tmp_path / "benchmark", "bench", bench_root, echo=None, device=tmp_path / "d")
    assert (tmp_path / "d" / rd.PIPELINE_LOGS / "r1.log").read_text().splitlines()[first] == "# bench"


def test_runner_failure_carries_the_tail(bench_root, tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_EXIT", "3")
    with pytest.raises(Halt) as e:
        run_pipeline(tmp_path / "c.yaml", tmp_path / "out", benchmark=bench_root, echo=None, tail=5,
                     device=tmp_path)
    message = str(e.value)
    assert "exited 3" in message and "error: fake failure" in message
    assert "line 0" not in message


def test_identify_without_an_identity_line_is_one_coded_error(bench_root, tmp_path):
    from perfrepair.data_handler.outbound.benchmark_runner import identify
    with pytest.raises(BenchmarkRunError, match=r"^identify_failed: pipeline --identify exited 2; last lines:"):
        identify(tmp_path / "c.yaml", False, benchmark=bench_root)


def test_runner_fails_when_no_manifest(bench_root, tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_NO_MANIFEST", "1")
    with pytest.raises(BenchmarkRunError, match="wrote no"):
        run_pipeline(tmp_path / "c.yaml", tmp_path / "out", benchmark=bench_root, echo=None, device=tmp_path)


def test_benchmark_root_lookup(bench_root, tmp_path, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(bench_root))
    assert benchmark_root() == bench_root.resolve()
    with pytest.raises(BenchmarkRunError, match="CRYPTOBENCH_ROOT"):
        benchmark_root(tmp_path / "nowhere")
    with pytest.raises(ValueError):
        run_pipeline(tmp_path / "c.yaml", tmp_path / "out", "measure", bench_root, device=tmp_path)


def test_without_cryptobench_root_the_checkout_holding_perf_repair_is_the_benchmark(monkeypatch):
    monkeypatch.delenv("CRYPTOBENCH_ROOT")
    assert benchmark_root() == Path(__file__).resolve().parents[3]


def test_the_child_never_sees_the_model_secrets(bench_root, tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("KEEP_ME", "1")
    run_pipeline(tmp_path / "c.yaml", tmp_path / "out", benchmark=bench_root, echo=None, device=tmp_path)
    env = json.loads((tmp_path / "out" / "argv.json").read_text())["env"]
    assert "KEEP_ME" in env and "ANTHROPIC_API_KEY" not in env


def test_a_hung_pipeline_is_killed_with_its_children_as_one_coded_stop(bench_root, tmp_path, monkeypatch):
    (tmp_path / "perfrepair.yaml").write_text("timeouts: {pipeline: 1}\n")
    install_stops(load(tmp_path / "perfrepair.yaml", {}, {}))
    monkeypatch.setenv("FAKE_HANG", "1")
    started = time.monotonic()
    with captured_events() as events, pytest.raises(Halt) as e:
        run_pipeline(tmp_path / "c.yaml", tmp_path / "out", "device", benchmark=bench_root, echo=None, device=tmp_path)
    assert time.monotonic() - started < 20 and e.value.code == "pipeline_timeout"
    [event] = [ev for ev in events if ev.data.get("code") == "pipeline_timeout"]
    assert event.item == "device" and event.data["seconds"] == 1 and "ran past 1s" in event.detail
