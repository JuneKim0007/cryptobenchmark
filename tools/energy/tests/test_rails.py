import pathlib, sys

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
    good = {"shortWindow": False, "netJoules": 1.0}
    assert energy.judge(dict(good), True)["valid"]
    bad = energy.judge({"shortWindow": True, "netJoules": -1.0}, False)
    assert bad["invalid"] == ["rails_unresponsive", "short_window", "net_not_positive"]


class SuspendedDeviceTrace:
    """Phase slices on MONOTONIC, rails on BOOTTIME, 1000 ns apart: a device that has slept."""

    def timed_phases(self):
        return [(100, 200)]

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
