"""thermal.json as the session hooks write it, byte for byte; parity/thermal.json is the file the Kotlin reader test reads too."""
import pathlib

from test_thermal_gate import CASE, Heat
from test_device_benchmark_flow import measured

GOLDEN = pathlib.Path(__file__).resolve().parents[3] / "parity/thermal.json"


def test_a_gated_run_with_one_unreadable_start_writes_the_shared_golden(tmp_path, monkeypatch):
    # hot start: 240 s of waiting before a; the fifth reading (a's start) is unreadable, so a carries a note
    Heat(monkeypatch, start=45.0, rise=0.1, cooling=0.05, unreadable=(5,))
    _phone, _files, problems, results = measured(tmp_path, monkeypatch, CASE)
    assert problems == []
    assert (results / "benchmark/thermal.json").read_text() == GOLDEN.read_text()
