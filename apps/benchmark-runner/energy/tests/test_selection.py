"""Which rails the sum reads: a real busy pre-flight's rails, cut to ten polls, and the fallbacks of the catalog rule."""
import pathlib

import pytest

import energy, preflight  # noqa: E402
from rails import selection  # noqa: E402
from rails.selection import Rails  # noqa: E402

BUSY = pathlib.Path(__file__).parent / "fixtures/busy_rails.pftrace"
SAMPLES = [(0, 0.0), (100, 1000.0), (200, 3000.0)]


def no_idle(_start, _end):
    return 0.0


def test_a_real_trace_sums_31_load_rails_by_raw_name_and_sets_the_battery_rail_apart():
    pytest.importorskip("perfetto")
    from rails.trace import Trace
    trace = Trace(BUSY)
    try:
        rails = trace.rails()
    finally:
        trace.close()
    assert list(rails.excluded) == ["VSYS_PWR_VBATT"] and len(rails.summed) == 31
    assert "S2M_VDD_CPU2" in rails.summed and not any(name.startswith("power.") for name in rails.summed)
    start, end = min(t for t, _ in rails.summed["S2M_VDD_CPU2"]), max(t for t, _ in rails.summed["S2M_VDD_CPU2"])
    result = energy.window(rails, start, end, no_idle, 1)
    assert result["joules"] == pytest.approx(sum(result["rails"].values()))
    assert set(result["excludedRails"]) == {"VSYS_PWR_VBATT"} and result["excludedHigh"]
    assert result["excludedShare"] == pytest.approx(result["excludedRails"]["VSYS_PWR_VBATT"] / result["joules"])
    document = preflight.capability(rails, rails, 1, 1, False)
    assert document["busyExcludedMicrojoules"] == pytest.approx(result["excludedRails"]["VSYS_PWR_VBATT"] * 1e6)


def test_a_rail_without_a_subsystem_or_of_an_unknown_one_is_summed():
    rails = selection.split({("power.a", "A", None): SAMPLES, ("power.b", "B", "Somewhere"): SAMPLES,
                             ("power.v", "V", "Battery"): SAMPLES}, frozenset({"Battery"}))
    assert rails == Rails({"A": SAMPLES, "B": SAMPLES}, {"V": SAMPLES})


@pytest.mark.parametrize("tracks", [
    {("power.a", None, None): SAMPLES},
    {("power.a", "A", "CPU"): SAMPLES, ("power.rails.a", "A", "CPU"): SAMPLES},
])
def test_a_rail_without_a_raw_name_or_with_a_repeated_one_is_refused(tracks):
    with pytest.raises(selection.Unidentified, match="rail_unidentified: power"):
        selection.split(tracks, frozenset())


def test_every_rail_excluded_reads_as_no_rails():
    rails = Rails({}, {"V": SAMPLES})
    with pytest.raises(energy.NotMeasured, match="no_rails"):
        energy.window(rails, 0, 200, no_idle, 1)
    assert not preflight.capability(rails, rails, 1, 1, False)["railsPresent"]
    with pytest.raises(SystemExit, match="no_rails"):
        preflight.ended({"idleMicrowatts": 1.0}, rails, 1.0)


def test_a_window_records_its_excluded_rails_beside_the_sum():
    result = energy.window(Rails({"A": SAMPLES}, {"V": [(0, 0.0), (200, 30.0)]}), 0, 200, no_idle, 1)
    assert (result["joules"], result["excludedRails"], result["excludedHigh"]) == (3000 / 1e6, {"V": 30 / 1e6}, False)
    assert result["excludedShare"] == pytest.approx(0.01)


@pytest.mark.parametrize("text", [None, "subsystems: Battery\n", "[a, b]\n", "subsystems: [1]\n"])
def test_a_missing_or_malformed_catalog_stops_with_its_code(tmp_path, text):
    path = tmp_path / "excluded.yaml"
    if text is not None:
        path.write_text(text)
    with pytest.raises(SystemExit, match="rails_catalog: "):
        selection.excluded_subsystems.__wrapped__(path)


def test_the_catalog_sets_apart_the_battery_subsystem():
    assert selection.excluded_subsystems() == frozenset({"Battery"})
