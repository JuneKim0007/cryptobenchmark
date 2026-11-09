
import pytest

import energy_stage


def test_effective_entries_inherit_the_run_capture(tmp_path):
    effective = tmp_path / "effective.yaml"
    effective.write_text("run: {harness: {energy: {capture: dry}}}\n"
                         "providers: {p: {t: {a: {}, b: [{harness: {energy: {capture: measured}}}]}}}\n")
    assert energy_stage.captures(effective) == {"dry", "measured"}


def test_no_entries_fall_back_to_the_run_capture(tmp_path):
    effective = tmp_path / "effective.yaml"
    effective.write_text("run: {}\n")
    assert energy_stage.captures(effective) == {"none"}


def test_a_run_has_one_source_and_rails_is_the_default(tmp_path):
    effective = tmp_path / "effective.yaml"
    effective.write_text("run: {}\n")
    assert type(energy_stage.source(effective, "py")).__name__ == "RailsSource"
    effective.write_text("run: {harness: {energy: {source: manafa}}}\nproviders: {p: {t: {a: {}}}}\n")
    assert type(energy_stage.source(effective, "py")).__name__ == "ManafaSource"


def test_entries_with_another_source_are_refused(tmp_path):
    effective = tmp_path / "effective.yaml"
    effective.write_text("run: {harness: {energy: {source: rails}}}\n"
                         "providers: {p: {t: {a: {}, b: {harness: {energy: {source: manafa}}}}}}\n")
    with pytest.raises(energy_stage.EnergyError, match="energy_sources_differ"):
        energy_stage.source(effective, "py")
