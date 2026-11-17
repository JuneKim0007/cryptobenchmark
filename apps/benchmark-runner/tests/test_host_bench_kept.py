"""A host BenchKt that dies keeps the rows it wrote: one bench_failed problem; with no row written the run fails as before."""
import json, pathlib, types

import pytest

from cryptobench.stages.measurement import benchmark  # noqa: E402
from cryptobench.stages.measurement.session import blocks  # noqa: E402
from failure import reported  # noqa: E402

OPTIONS = types.SimpleNamespace(stacktrace=False, stream=False)
DOCUMENT = {"run": {"processRepetitions": 1}}
ONE_BLOCK = lambda folder: blocks.Blocks(folder, 10, 1, {})


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
    written = benchmark.host_cases(OPTIONS, DOCUMENT, "c", "t", "e", tmp_path, tmp_path, {}, problems, ONE_BLOCK(tmp_path))
    assert json.loads(written[0].read_text())["cases"] == [{"id": "a"}]
    assert problems == ["bench_failed: error: Execution failed for task ':run'"]


def test_a_death_before_any_row_fails_the_run_and_an_earlier_runs_file_is_not_taken_for_this_ones(tmp_path, monkeypatch):
    (tmp_path / "benchmark.json").write_text("{}")
    monkeypatch.setattr(benchmark.gradle_runner, "run", dying([]))
    with pytest.raises(SystemExit) as stopped, reported():
        benchmark.host_cases(OPTIONS, DOCUMENT, "c", "t", "e", tmp_path, tmp_path, {}, [], ONE_BLOCK(tmp_path))
    assert stopped.value.code == 1


def test_a_host_rerun_keeps_the_recorded_blocks_and_benches_only_the_rest(tmp_path, monkeypatch):
    benched = []

    def bench(arguments, *_options, failed, **_keywords):
        into = pathlib.Path(arguments.split()[3])
        if into.name == "process-3" and not benched.count("stop"):
            benched.append("stop")
            raise KeyboardInterrupt()
        benched.append(into.name)
        into.mkdir(parents=True, exist_ok=True)
        (into / "benchmark.json").write_text(json.dumps({"runtime": {}, "cases": [{"id": "a"}]}))
        return []
    monkeypatch.setattr(benchmark.gradle_runner, "run", bench)
    monkeypatch.setattr(benchmark.passes, "merge_runs", lambda *_arguments: None)
    document, in_blocks = {"run": {"processRepetitions": 3}}, blocks.Blocks(tmp_path, 1, 3, {"code": "c"})
    with pytest.raises(KeyboardInterrupt):
        benchmark.host_cases(OPTIONS, document, "c", "t", "e", tmp_path, tmp_path, {}, [], in_blocks)
    written = benchmark.host_cases(OPTIONS, document, "c", "t", "e", tmp_path, tmp_path, {}, [], in_blocks)
    assert benched == ["process-1", "process-2", "stop", "process-3"]
    assert [p.parent.name for p in written] == ["process-1", "process-2", "process-3"]
    assert sorted(p.name for p in (tmp_path / "blocks").iterdir()) == ["block-1.yaml", "block-2.yaml", "block-3.yaml"]
