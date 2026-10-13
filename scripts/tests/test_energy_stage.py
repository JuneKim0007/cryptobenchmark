import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
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
