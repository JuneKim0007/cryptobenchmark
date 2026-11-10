import json

import run_counts


def process(tmp_path, name, iters, calls, gate):
    case = {"id": "a", "metrics": {"timeNs": {"iterations": calls, "runs": [1.0] * iters}}, "gate": gate}
    file = tmp_path / name
    file.write_text(json.dumps({"cases": [case, {"id": "b", "metrics": {"timeNs": {"iterations": 7, "runs": [1.0]}}}]}))
    return file


def test_runs_iters_calls_discards_and_waits_come_from_every_process(tmp_path):
    files = [process(tmp_path, "1.json", 50, 40, {"waitedSeconds": 180.5, "discards": 1}), process(tmp_path, "2.json", 50, 60, {"waitedSeconds": 0.0, "discards": 0})]
    assert run_counts.rows(files) == [("a", 2, "50", "40-60", 1, 180.5), ("b", 2, "1", "7", 0, 0.0)]


def test_the_table_is_written_with_the_session_totals(tmp_path):
    run_counts.write(tmp_path / "out", [process(tmp_path, "1.json", 50, 40, {"waitedSeconds": 12.5, "discards": 2})])
    text = (tmp_path / "out/run-counts.md").read_text()
    assert "| a | 1 | 50 | 40 | 2 | 12.5 |" in text and "2 runs in all, 2 discarded for heat, 12.5 s waited for temperature" in text
