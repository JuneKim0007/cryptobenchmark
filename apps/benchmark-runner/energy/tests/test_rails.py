import json, pathlib, sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import energy, preflight  # noqa: E402
from rails import counters  # noqa: E402

SAMPLES = [(0, 0.0), (100, 1000.0), (200, 3000.0)]


def test_interpolates_inside_a_poll_interval():
    assert counters.at(SAMPLES, 50) == 500.0
    assert counters.between(SAMPLES, 50, 150) == pytest.approx(1500.0)


def test_refuses_a_window_outside_the_samples():
    with pytest.raises(ValueError, match="uncovered"):
        counters.between(SAMPLES, 50, 250)


def test_window_reports_joules_net_of_idle_and_per_operation():
    r = energy.window({"a": SAMPLES, "b": SAMPLES}, 0, 200, idle_uj_per_ns=5.0, operations=4)
    assert r["joules"] == pytest.approx(6000 / 1e6)
    assert r["netJoules"] == pytest.approx((6000 - 1000) / 1e6)
    assert r["joulesPerOperation"] == pytest.approx(5000 / 1e6 / 4)
    assert r["polls"] == 3 and r["shortWindow"]


def test_rails_that_do_not_respond_to_load_are_flagged():
    flat = {"r": [(0, 0.0), (10, 1500.0)]}
    hot = {"r": [(0, 0.0), (10, 6000.0)]}
    assert not preflight.capability(flat, flat, 2, False)["railsResponsive"]
    assert preflight.capability(flat, hot, 2, False)["railsResponsive"]
    assert not preflight.capability({}, {}, 2, False)["railsPresent"]


def test_a_case_is_valid_only_when_every_check_holds():
    good = {"shortWindow": False, "netJoules": 1.0, "operations": 4, "joulesPerOperation": 0.25}
    assert energy.judge(dict(good), True)["valid"]
    bad = energy.judge({"shortWindow": True, "netJoules": -1.0, "operations": 4, "joulesPerOperation": -0.25}, False)
    assert bad["invalid"] == ["rails_unresponsive", "short_window", "net_not_positive"]


def phase(start, end):
    return {"start": start, "end": end, "runs": [(0, start, end)], "sleeps": []}


class SuspendedDeviceTrace:
    """Phase slices on MONOTONIC, rails on BOOTTIME, 1000 ns apart: a device that has slept."""

    def timed_phases(self):
        return [phase(100, 200)]

    def boot_minus_monotonic(self):
        return 1000

    def rails(self):
        return {"r": [(t, float(t)) for t in range(1000, 1300, 10)]}

    def close(self):
        pass


def test_a_measured_window_is_moved_onto_the_rails_clock(tmp_path):
    data = tmp_path / "data.json"
    data.write_text('{"benchmarks": [{"name": "measure[c1]", "repeatIterations": 10, "metrics": {"timeNs": {"runs": [1, 2]}},'
                    ' "profilerOutputs": [{"type": "PerfettoTrace", "filename": "c1.trace"}]}]}')
    prepared = tmp_path / "prepared.yaml"
    prepared.write_text("cases: [{id: c1, harness: {energy: {capture: measured}}}]\n")
    (tmp_path / "c1.trace").write_text("")
    result = energy.measured_cases(data, prepared, tmp_path, 0.0, lambda path: SuspendedDeviceTrace())["c1"]
    assert result["windowSeconds"] == pytest.approx(100 / 1e9) and result["joules"] == pytest.approx(100 / 1e6)
    assert result["clockOffsetNs"] == 1000


class RailsStopEarlyTrace(SuspendedDeviceTrace):
    """The rail capture ended before the timed phase did (seen on a Pixel 10)."""

    def rails(self):
        return {"r": [(t, float(t)) for t in range(1000, 1150, 10)]}


def test_a_phase_past_the_last_rail_sample_is_one_invalid_case_not_a_failed_run(tmp_path):
    data = tmp_path / "data.json"
    data.write_text('{"benchmarks": [{"name": "measure[c1]", "repeatIterations": 10, "metrics": {"timeNs": {"runs": [1]}},'
                    ' "profilerOutputs": [{"type": "PerfettoTrace", "filename": "c1.trace"}]}]}')
    prepared = tmp_path / "prepared.yaml"
    prepared.write_text("cases: [{id: c1, harness: {energy: {capture: measured}}}]\n")
    (tmp_path / "c1.trace").write_text("")
    result = energy.measured_cases(data, prepared, tmp_path, 0.0, lambda path: RailsStopEarlyTrace())["c1"]
    assert result["joulesPerOperation"] is None
    assert energy.judge(result, True)["invalid"] == ["window_uncovered"]


class Rows(list):
    pass


class SnapshotProcessor:
    """The first snapshot holds only BOOTTIME; the second holds both clocks."""

    def query(self, sql):
        row = type("R", (), {})
        r = row(); r.offset = 700
        return Rows([r]) if "BOOTTIME" in sql and "MONOTONIC" in sql and "join" in sql else Rows()


def test_the_offset_comes_from_the_first_snapshot_with_both_clocks():
    pytest.importorskip("perfetto")
    from rails.trace import Trace
    trace = Trace.__new__(Trace)
    trace.processor = SnapshotProcessor()
    assert trace.boot_minus_monotonic() == 700


def _benchmark(case, trace, runs=1):
    return {"name": f"measure[{case}]", "repeatIterations": 10, "metrics": {"timeNs": {"runs": [1] * runs}},
            "profilerOutputs": [{"type": "PerfettoTrace", "filename": trace}]}


class Phases(SuspendedDeviceTrace):

    def __init__(self, phases=((100, 200),), offset=1000, rails=None):
        self.phases, self.offset, self.rail_samples = [phase(*p) if isinstance(p, tuple) else p for p in phases], offset, rails

    def timed_phases(self):
        return self.phases

    def boot_minus_monotonic(self):
        return self.offset

    def rails(self):
        return super().rails() if self.rail_samples is None else self.rail_samples


class Broken(SuspendedDeviceTrace):

    def timed_phases(self):
        raise RuntimeError("truncated\ntrace")


@pytest.mark.parametrize("trace, reason", [
    (None, "trace_not_pulled"),
    (Phases(phases=[]), "timed_phases: 0"),
    (Phases(phases=[(100, 200), (300, 400)]), "timed_phases: 2"),
    (Phases(offset=None), "no_clock_snapshot"),
    (Phases(rails={}), "no_rails"),
    (Phases(phases=[(200, 100)]), "empty_window"),
    (Phases(phases=[{"start": 100, "end": 200, "runs": [], "sleeps": []}]), "no_measurement_slices"),
    (Broken(), "trace_unreadable: truncated trace"),
])
def test_one_bad_measured_case_is_its_own_invalid_reason_and_the_others_still_measure(tmp_path, trace, reason):
    data = tmp_path / "data.json"
    data.write_text(json.dumps({"benchmarks": [_benchmark("bad", "bad.trace"), _benchmark("good", "good.trace", runs=2)]}))
    prepared = tmp_path / "prepared.yaml"
    prepared.write_text("run: {harness: {energy: {capture: measured}}}\ncases: [{id: bad}, {id: good}]\n")
    (tmp_path / "good.trace").write_text("")
    if trace is not None:
        (tmp_path / "bad.trace").write_text("")
    traces = {"good.trace": SuspendedDeviceTrace(), "bad.trace": trace}
    cases = energy.measured_cases(data, prepared, tmp_path, 0.0, lambda path: traces[path.name])
    bad, good = (energy.judge(cases[c], True) for c in ("bad", "good"))
    assert bad["invalid"] == [reason] and bad["joulesPerOperation"] is None and bad["operations"] == 10
    assert good["joulesPerOperation"] is not None and good["operations"] == 20 and "notMeasured" not in good


def test_a_dry_marker_without_a_call_count_is_invalid_and_the_other_marker_measures(tmp_path):
    class Dry(SuspendedDeviceTrace):
        def markers(self):
            return {"lost": (1000, 1200), "kept": (1000, 1200)}
    calls = tmp_path / "calls.yaml"
    calls.write_text("kept: 5\n")
    cases = energy.dry_cases(tmp_path / "dry.pftrace", calls, 0.0, lambda path: Dry())
    assert energy.judge(cases["lost"], True)["invalid"] == ["no_call_count"]
    assert cases["kept"]["joulesPerOperation"] is not None


def test_a_case_without_operations_is_never_valid():
    result = energy.window({"r": SAMPLES}, 0, 200, 0.0, 0)
    assert result["joulesPerOperation"] is None
    assert energy.judge(result, True)["invalid"][0] == "no_operations"


def test_end_before_start_is_an_empty_window_not_an_uncovered_one():
    with pytest.raises(counters.EmptyWindow):
        counters.between(SAMPLES, 150, 50)
