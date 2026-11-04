import pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import energy  # noqa: E402
from capture import capture  # noqa: E402


def test_a_case_overrides_the_run_and_the_run_overrides_none():
    assert capture(None) == "none"
    assert capture({"harness": {"energy": {"capture": "dry"}}}) == "dry"
    assert capture({"harness": {}}, "measured") == "measured"


def test_prepared_cases_inherit_the_run_capture(tmp_path):
    prepared = tmp_path / "prepared.yaml"
    prepared.write_text("run: {harness: {energy: {capture: dry}}}\n"
                        "cases:\n- {id: a}\n- {id: b, harness: {energy: {capture: measured}}}\n")
    assert energy.captures(prepared) == {"a": "dry", "b": "measured"}
