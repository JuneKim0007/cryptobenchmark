"""The energy window of a case that slept twice for heat, from a real Pixel trace's slices: the kept runs lie between the sleeps."""
import json, pathlib

import pytest

import energy  # noqa: E402

SHAPE = json.loads((pathlib.Path(__file__).parent / "fixtures/thermal_sleep_phase.json").read_text())


class RealShape:
    """Benchmark Time, its 500 measurement runs and two 90 s sleeps as recorded; rails every 100 ms over the recorded rail span."""

    def timed_phases(self):
        runs = [(int(name.split()[-1]), start, end) for name, start, end in SHAPE["runs"]]
        return [{"start": SHAPE["phase"][0], "end": SHAPE["phase"][1], "runs": runs, "sleeps": [tuple(s) for s in SHAPE["sleeps"]]}]

    def boot_minus_monotonic(self):
        return SHAPE["bootMinusMonotonic"]

    def rails(self):
        first, last, _count = SHAPE["rails"]
        return {"power.a": [(t, t / 1e6) for t in range(first, last, 100_000_000)]}

    def close(self):
        pass


def test_the_window_is_the_kept_runs_between_the_sleeps_and_the_case_is_flagged(tmp_path):
    data = tmp_path / "data.json"
    data.write_text(json.dumps({"benchmarks": [{"name": "measure[c]", "repeatIterations": 10, "metrics": {"timeNs": {"runs": [1] * SHAPE["keptRuns"]}},
                                                "profilerOutputs": [{"type": "PerfettoTrace", "filename": "c.trace"}]}]}))
    prepared = tmp_path / "prepared.yaml"
    prepared.write_text("cases: [{id: c, harness: {energy: {capture: measured}}}]\n")
    (tmp_path / "c.trace").write_bytes(b"x" * 7)
    result = energy.judge(energy.measured_cases(data, prepared, tmp_path, 0.0, lambda _path: RealShape())["c"], True)
    assert result["windowSeconds"] == pytest.approx(56.43, abs=0.01)
    assert result["polls"] > 500 and result["valid"]
    assert result["heatSleepAfterKeptRuns"] is True and result["traceBytes"] == 7 and result["traceLarge"] is False


def test_every_kept_run_is_inside_the_window_and_both_sleeps_outside():
    start, end, slept = energy.kept_runs(RealShape().timed_phases()[0])
    numbers = [n for n, s, e in RealShape().timed_phases()[0]["runs"] if start <= s and e <= end]
    assert numbers == list(range(SHAPE["keptRuns"])) and slept
    assert all(e <= start or s >= end for s, e in SHAPE["sleeps"])
