import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from stages import not_measured  # noqa: E402


def test_a_planned_timed_case_absent_from_the_results_is_one_line_and_one_record(tmp_path, capsys):
    prepared, benchmark = tmp_path / "prepared.yaml", tmp_path / "benchmark.json"
    prepared.write_text("run: {harness: {energy: {capture: measured}}}\n"
                        "cases: [{id: kept}, {id: lost}, {id: dry, harness: {energy: {capture: dry}}}]\n")
    benchmark.write_text(json.dumps({"cases": [{"id": "kept"}]}))
    problems = []
    not_measured.report(prepared, benchmark, problems)
    assert problems == ["not_measured: lost"]
    assert capsys.readouterr().out == "not_measured: lost\n"


def test_a_run_that_measured_every_planned_case_records_nothing(tmp_path):
    prepared, benchmark = tmp_path / "prepared.yaml", tmp_path / "benchmark.json"
    prepared.write_text("cases: [{id: a}]\n")
    benchmark.write_text(json.dumps({"cases": [{"id": "a"}]}))
    assert not_measured.lines(prepared, benchmark) == []
