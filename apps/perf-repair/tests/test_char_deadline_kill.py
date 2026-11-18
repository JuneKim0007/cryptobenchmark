"""Characterization (Py-P6), changed: a pipeline past its timeout gets SIGTERM with its group and writes its partial manifest; one deaf to it is
SIGKILLed once the grace has passed. Before, it was SIGKILLed at once and wrote none."""
import time

import pytest

from cryptobench.shared.errors.halt import Halt
from perfrepair.config.load import load
from perfrepair.config.stops import install_stops
from perfrepair.data_handler.outbound import benchmark_runner, run_pipeline
from test_outbound import bench_root  # noqa: F401

TRAPS_TERM = """import os, pathlib, signal, sys, time
results = pathlib.Path(sys.argv[sys.argv.index("--results") + 1])
results.mkdir(parents=True, exist_ok=True)
def stopped(*_):
    (results / "partial.yaml").write_text("partial: {reason: interrupted}\\n")
    sys.exit(130)
signal.signal(signal.SIGTERM, %s)
(results / "pid").write_text(str(os.getpid()))
print("measuring", flush=True)
time.sleep(60)
"""


def timed_out(bench_root, tmp_path, handler):  # noqa: F811
    (bench_root / "apps/benchmark-runner/pipeline.py").write_text(TRAPS_TERM % handler)
    (tmp_path / "perfrepair.yaml").write_text("timeouts: {pipeline: 1}\n")
    install_stops(load(tmp_path / "perfrepair.yaml", {}, {}))
    started = time.monotonic()
    with pytest.raises(Halt) as stop:
        run_pipeline(tmp_path / "c.yaml", tmp_path / "out", "device", benchmark=bench_root, echo=None, device=tmp_path)
    assert stop.value.code == "pipeline_timeout" and "stopped with its children" in str(stop.value)
    assert (tmp_path / "out/pid").is_file()
    return time.monotonic() - started


def test_a_pipeline_timeout_stops_it_with_sigterm_and_its_partial_manifest_is_written(bench_root, tmp_path):  # noqa: F811
    assert timed_out(bench_root, tmp_path, "stopped") < 20
    assert (tmp_path / "out/partial.yaml").is_file()


def test_a_pipeline_deaf_to_sigterm_is_killed_once_the_grace_has_passed(bench_root, tmp_path, monkeypatch):  # noqa: F811
    monkeypatch.setattr(benchmark_runner, "PIPELINE_GRACE_SECONDS", 1)
    assert 2 <= timed_out(bench_root, tmp_path, "signal.SIG_IGN") < 20
    assert not (tmp_path / "out/partial.yaml").exists()
