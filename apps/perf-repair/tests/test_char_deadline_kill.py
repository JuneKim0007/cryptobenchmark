"""Characterization (Py-P6): a pipeline past its timeout is SIGKILLed with its group at once; it never gets a SIGTERM, so it writes no partial
manifest."""
import time

import pytest

from cryptobench.shared.errors.halt import Halt
from perfrepair.config.load import load
from perfrepair.config.stops import install_stops
from perfrepair.data_handler.outbound import run_pipeline
from test_outbound import bench_root  # noqa: F401

TRAPS_TERM = """import os, pathlib, signal, sys, time
results = pathlib.Path(sys.argv[sys.argv.index("--results") + 1])
results.mkdir(parents=True, exist_ok=True)
def stopped(*_):
    (results / "partial.yaml").write_text("partial: {reason: interrupted}\\n")
    sys.exit(130)
signal.signal(signal.SIGTERM, stopped)
(results / "pid").write_text(str(os.getpid()))
print("measuring", flush=True)
time.sleep(60)
"""


def test_today_a_pipeline_timeout_kills_at_once_and_no_partial_manifest_is_written(bench_root, tmp_path):  # noqa: F811
    (bench_root / "apps/benchmark-runner/pipeline.py").write_text(TRAPS_TERM)
    (tmp_path / "perfrepair.yaml").write_text("timeouts: {pipeline: 1}\n")
    install_stops(load(tmp_path / "perfrepair.yaml", {}, {}))
    started = time.monotonic()
    with pytest.raises(Halt) as stop:
        run_pipeline(tmp_path / "c.yaml", tmp_path / "out", "device", benchmark=bench_root, echo=None, device=tmp_path)
    assert stop.value.code == "pipeline_timeout" and time.monotonic() - started < 20
    assert (tmp_path / "out/pid").is_file() and not (tmp_path / "out/partial.yaml").exists()
