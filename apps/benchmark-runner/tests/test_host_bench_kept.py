"""A host BenchKt that dies keeps the rows it wrote: one bench_failed problem; with no row written the run fails as before."""
import json, pathlib, types

import pytest

from stages import benchmark  # noqa: E402

OPTIONS = types.SimpleNamespace(stacktrace=False, stream=False)
DOCUMENT = {"run": {"processRepetitions": 1}}


def dying(rows):
    def run(arguments, *_options, failed, **_keywords):
        into = pathlib.Path(arguments.split()[3])
        if rows:
            (into / "benchmark.json").write_text(json.dumps({"runtime": {}, "cases": rows}))
        failed("error: Execution failed for task ':run'")
        return []
    return run


def test_rows_written_before_the_jvm_died_are_kept_and_the_death_is_a_problem(tmp_path, monkeypatch):
    monkeypatch.setattr(benchmark.gradle_runner, "run", dying([{"id": "a"}]))
    problems = []
    written = benchmark.host_cases(OPTIONS, DOCUMENT, "c", "t", "e", tmp_path, tmp_path, {}, problems)
    assert json.loads(written[0].read_text())["cases"] == [{"id": "a"}]
    assert problems == ["bench_failed: error: Execution failed for task ':run'"]


def test_a_death_before_any_row_fails_the_run_and_an_earlier_runs_file_is_not_taken_for_this_ones(tmp_path, monkeypatch):
    (tmp_path / "benchmark.json").write_text("{}")
    monkeypatch.setattr(benchmark.gradle_runner, "run", dying([]))
    with pytest.raises(SystemExit) as stopped:
        benchmark.host_cases(OPTIONS, DOCUMENT, "c", "t", "e", tmp_path, tmp_path, {}, [])
    assert stopped.value.code == 1
