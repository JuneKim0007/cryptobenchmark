import json

import pytest
import yaml

import energy, preflight, rails_run  # noqa: E402
from rails import counters  # noqa: E402
from rails.selection import Rails  # noqa: E402

SAMPLES = [(0, 0.0), (100, 1000.0), (200, 3000.0)]


def NO_IDLE(_start, _end):
    return 0.0


def test_interpolates_inside_a_poll_interval():
    assert counters.at(SAMPLES, 50) == 500.0
    assert counters.between(SAMPLES, 50, 150) == pytest.approx(1500.0)


def test_refuses_a_window_outside_the_samples():
    with pytest.raises(ValueError, match="uncovered"):
        counters.between(SAMPLES, 50, 250)


def test_window_reports_joules_net_of_idle_and_per_operation():
    r = energy.window(Rails({"a": SAMPLES, "b": SAMPLES}, {}), 0, 200, idle=lambda a, b: 5.0 * (b - a), operations=4)
    assert r["joules"] == pytest.approx(6000 / 1e6)
    assert r["netJoules"] == pytest.approx((6000 - 1000) / 1e6)
    assert r["joulesPerOperation"] == pytest.approx(5000 / 1e6 / 4)
    assert r["polls"] == 3 and r["shortWindow"]


def test_rails_that_do_not_respond_to_load_are_flagged():
    flat = Rails({"r": [(0, 0.0), (10, 1500.0)]}, {})
    hot = Rails({"r": [(0, 0.0), (10, 6000.0)]}, {})
    assert not preflight.capability(flat, flat, 2, 2, False)["railsResponsive"]
    assert preflight.capability(flat, hot, 2, 2, False)["railsResponsive"]
    assert not preflight.capability(Rails({}, {}), Rails({}, {}), 2, 2, False)["railsPresent"]


def spanning(seconds, microjoules):
    return Rails({"r": [(0, 0.0), (int(seconds * 1e9), microjoules)]}, {})


def test_responsiveness_compares_power_over_the_spans_the_samples_cover():
    idle = spanning(40, 40000.0)
    assert preflight.capability(idle, spanning(3, 6000.0), 40, 3, False)["railsResponsive"]
    assert not preflight.capability(idle, spanning(6, 6000.0), 40, 3, False)["railsResponsive"]
    document = preflight.capability(idle, spanning(3, 6000.0), 40, 3, False)
    assert (document["idleWindowSeconds"], document["busyWindowSeconds"], document["idleSpanSeconds"]) == (40, 3, 40.0)
    assert document["idleMicrowatts"] == pytest.approx(1000.0)


def test_idle_power_is_over_the_sampled_span_not_the_configured_length():
    document = preflight.capability(spanning(100, 50000.0), spanning(3, 9e6), 120, 3, False, {"start": None, "end": None})
    assert (document["idleSpanSeconds"], document["idleMicrowatts"]) == (100.0, 500.0)
    assert document["idleSkin"] == {"start": None, "end": None}


def energy_with(folder, edit):
    out = folder / "energy.json"
    arguments = rails_run.arguments(folder, out)
    capability = folder / "energy.yaml"
    capability.write_text(edit(capability.read_text()))
    energy.main(arguments)
    return json.loads(out.read_text())["cases"]


def test_measured_and_dry_subtract_the_one_idle_power_of_the_idle_window(tmp_path, monkeypatch):
    rails_run.install_fake_trace(monkeypatch)
    narrow = energy_with(tmp_path, lambda text: text)
    wide = energy_with(tmp_path, lambda text: text.replace("idleMicrowatts: 1000.0", "idleMicrowatts: 500.0"))
    for case in ("m1", "d1"):
        idle = narrow[case]["joules"] - narrow[case]["netJoules"]
        assert wide[case]["joules"] - wide[case]["netJoules"] == pytest.approx(idle / 2)


def test_an_energy_yaml_of_another_schema_is_refused(tmp_path, monkeypatch):
    rails_run.install_fake_trace(monkeypatch)
    with pytest.raises(SystemExit, match="unsupported_schema_version: energy.yaml: 3, this build reads 4"):
        energy_with(tmp_path, lambda text: text.replace("schemaVersion: 4", "schemaVersion: 3"))


START = {"idleMicrowatts": 1000.0, "idleBoottimeNs": 1000}
END = {"idleEndMicrowatts": 2000.0, "idleEndBoottimeNs": 3000}


def test_idle_is_the_line_between_the_start_and_end_readings_at_each_windows_midpoint():
    idle, baseline = energy.idle_of(START | END)
    assert baseline == "interpolated"
    # 1e-6 uJ/ns at 1000 ns, 2e-6 at 3000 ns: the window 1500..2500 is centred on 2000, 1.5e-6 uJ/ns over 1000 ns
    assert idle(1500, 2500) == pytest.approx(1.5e-3)
    assert idle(1000, 1010) == pytest.approx(1e-6 * (1 + 5 / 2000) * 10)


def test_without_an_end_reading_idle_is_the_start_reading_and_marked():
    for capability in (START, START | END | {"idleEndBoottimeNs": None}, START | END | {"idleEndBoottimeNs": 1000}):
        idle, baseline = energy.idle_of(capability)
        assert baseline == "idle_start_only" and idle(1500, 2500) == pytest.approx(1e-3)


def test_the_end_reading_joins_energy_yaml_with_its_time_the_drift_and_the_skin(tmp_path, monkeypatch, capsys):
    rails_run.install_fake_trace(monkeypatch)
    rails_run.inputs(tmp_path)
    skin = {"start": {"sensor": "VIRTUAL-SKIN", "celsius": 31.5}, "end": {"sensor": "VIRTUAL-SKIN", "celsius": 31.9}}
    rails_run.run_end(tmp_path, skin=("--skin", json.dumps(skin)))
    document = yaml.safe_load((tmp_path / "energy.yaml").read_text())
    assert (document["idleEndMicrojoules"], document["idleEndWindowSeconds"], document["idleEndBoottimeNs"]) == (19750.0, 3.0, 4950)
    # the fake rails span 1000..8900 ns: the power is over that span, not over the 3 s asked for
    assert document["idleEndSpanSeconds"] == pytest.approx(7.9e-6)
    assert document["idleEndMicrowatts"] == pytest.approx(19750 / 7.9e-6)
    assert document["idleDriftPercent"] == pytest.approx((19750 / 7.9e-6 / 1000 - 1) * 100)
    assert document["idleEndSkin"] == skin
    assert "skin 31.5 C -> 31.9 C (VIRTUAL-SKIN)" in capsys.readouterr().out


def test_an_end_trace_without_rails_is_refused_and_energy_yaml_is_kept(tmp_path, monkeypatch):
    rails_run.install_fake_trace(monkeypatch)
    rails_run.inputs(tmp_path)
    before = (tmp_path / "energy.yaml").read_text()
    with pytest.raises(SystemExit, match="no_rails"):
        preflight.ended(yaml.safe_load(before), Rails({}, {}), 3.0)
    assert (tmp_path / "energy.yaml").read_text() == before


def test_measured_and_dry_read_the_same_interpolated_idle(tmp_path, monkeypatch):
    rails_run.install_fake_trace(monkeypatch)
    out = tmp_path / "energy.json"
    arguments = rails_run.arguments(tmp_path, out)
    rails_run.run_end(tmp_path)
    energy.main(arguments)
    document = json.loads(out.read_text())
    assert document["idleBaseline"] == "interpolated"
    idle, _ = energy.idle_of(yaml.safe_load((tmp_path / "energy.yaml").read_text()))
    for case, (start, end) in (("m1", (1500, 5500)), ("d1", (2000, 7000))):
        assert document["cases"][case]["idleJoules"] == pytest.approx(idle(start, end) / 1e6)
        assert document["cases"][case]["joules"] - document["cases"][case]["netJoules"] == pytest.approx(idle(start, end) / 1e6)


def phase(start, end):
    return {"start": start, "end": end, "runs": [(0, start, end)], "sleeps": []}


class SuspendedDeviceTrace:
    """Phase slices on MONOTONIC, rails on BOOTTIME, 1000 ns apart: a device that has slept."""

    def timed_phases(self):
        return [phase(100, 200)]

    def boot_minus_monotonic(self):
        return 1000

    def rails(self):
        return Rails({"r": [(t, float(t)) for t in range(1000, 1300, 10)]}, {})

    def close(self):
        pass


def test_a_measured_window_is_moved_onto_the_rails_clock(tmp_path):
    data = tmp_path / "data.json"
    data.write_text('{"benchmarks": [{"name": "measure[c1]", "repeatIterations": 10, "metrics": {"timeNs": {"runs": [1, 2]}},'
                    ' "profilerOutputs": [{"type": "PerfettoTrace", "filename": "c1.trace"}]}]}')
    prepared = tmp_path / "prepared.yaml"
    prepared.write_text("cases: [{id: c1, harness: {energy: {capture: measured}}}]\n")
    (tmp_path / "c1.trace").write_text("")
    result = energy.measured_cases(data, prepared, tmp_path, NO_IDLE, lambda path: SuspendedDeviceTrace())["c1"]
    assert result["windowSeconds"] == pytest.approx(100 / 1e9) and result["joules"] == pytest.approx(100 / 1e6)
    assert result["clockOffsetNs"] == 1000


class RailsStopEarlyTrace(SuspendedDeviceTrace):
    """The rail capture ended before the timed phase did (seen on a device)."""

    def rails(self):
        return Rails({"r": [(t, float(t)) for t in range(1000, 1150, 10)]}, {})


def test_a_phase_past_the_last_rail_sample_is_one_invalid_case_not_a_failed_run(tmp_path):
    data = tmp_path / "data.json"
    data.write_text('{"benchmarks": [{"name": "measure[c1]", "repeatIterations": 10, "metrics": {"timeNs": {"runs": [1]}},'
                    ' "profilerOutputs": [{"type": "PerfettoTrace", "filename": "c1.trace"}]}]}')
    prepared = tmp_path / "prepared.yaml"
    prepared.write_text("cases: [{id: c1, harness: {energy: {capture: measured}}}]\n")
    (tmp_path / "c1.trace").write_text("")
    result = energy.measured_cases(data, prepared, tmp_path, NO_IDLE, lambda path: RailsStopEarlyTrace())["c1"]
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
    (Phases(rails=Rails({}, {})), "no_rails"),
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
    cases = energy.measured_cases(data, prepared, tmp_path, NO_IDLE, lambda path: traces[path.name])
    bad, good = (energy.judge(cases[c], True) for c in ("bad", "good"))
    assert bad["invalid"] == [reason] and bad["joulesPerOperation"] is None and bad["operations"] == 10
    assert good["joulesPerOperation"] is not None and good["operations"] == 20 and "notMeasured" not in good


def test_a_dry_marker_without_a_call_count_is_invalid_and_the_other_marker_measures(tmp_path):
    class Dry(SuspendedDeviceTrace):
        def markers(self):
            return {"lost": (1000, 1200), "kept": (1000, 1200)}
    calls = tmp_path / "calls.yaml"
    calls.write_text("kept: 5\n")
    cases = energy.dry_cases(tmp_path / "dry.pftrace", calls, NO_IDLE, lambda path: Dry())
    assert energy.judge(cases["lost"], True)["invalid"] == ["no_call_count"]
    assert cases["kept"]["joulesPerOperation"] is not None


def test_an_empty_energy_dry_file_reads_as_no_call_counts(tmp_path):
    class Dry(SuspendedDeviceTrace):
        def markers(self):
            return {}
    calls = tmp_path / "calls.yaml"
    calls.write_text("")
    assert energy.dry_cases(tmp_path / "dry.pftrace", calls, NO_IDLE, lambda path: Dry()) == {}


def test_a_case_without_operations_is_never_valid():
    result = energy.window(Rails({"r": SAMPLES}, {}), 0, 200, NO_IDLE, 0)
    assert result["joulesPerOperation"] is None
    assert energy.judge(result, True)["invalid"][0] == "no_operations"


def test_end_before_start_is_an_empty_window_not_an_uncovered_one():
    with pytest.raises(counters.EmptyWindow):
        counters.between(SAMPLES, 150, 50)
