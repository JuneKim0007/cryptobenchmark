"""The exact text of the runner's warning: and check: lines reachable without a device, as owner scripts and compare.py read them."""
import pytest
import yaml

from device import facts
from results import layout
from stages import benchmark, capture_files, check
from stages.measuring import record
from fake_phone import Phone
from test_check_stage import RESULT
from test_host_bench_kept import DOCUMENT, OPTIONS, dying
from test_session_hooks import Recorded, session


def test_a_results_root_in_temp(tmp_path, capsys):
    layout.warn_if_temp(tmp_path)
    assert capsys.readouterr().out == (f"warning: results_in_temp: {tmp_path} is under a temporary folder the system may wipe; "
                                       "keep results elsewhere\n")


def test_a_reuse_that_probed_again(tmp_path, capsys):
    capture_files.reprobed(set(), tmp_path / "probe_20260102T000000Z.yaml")
    assert capsys.readouterr().out == (f"warning: discovery_reprobed: no capture in {tmp_path} fits this JVM's runtime; "
                                       "--discovery reuse probed again\n")


def test_pinning_unknown(tmp_path, capsys):
    facts.pinning(tmp_path / "missing.apk", "arm64-v8a")
    assert capsys.readouterr().out == f"warning: pinning_unknown: {tmp_path / 'missing.apk'} absent; facts.yaml records pinning null\n"


def test_a_cpu_pin_that_failed(tmp_path, capsys):
    benchmark.paths.Measurement(tmp_path).cpu_pins.write_text(yaml.safe_dump({"a": {"failed": "sched_setaffinity EINVAL"}, "b": {"cpus": [7]}}))
    record({}, tmp_path, {"none"}, object())
    assert capsys.readouterr().out == "warning: cpu_pin_failed: a: sched_setaffinity EINVAL\n"


def test_the_check_summary_lines(tmp_path, capsys):
    result = tmp_path / "check.yaml"
    result.write_text(yaml.safe_dump(RESULT, sort_keys=False))
    check.summary(result)
    assert capsys.readouterr().out.splitlines() == [
        "check:     1 pass, 1 fail, 1 notRun of 3 cases",
        "check:     knownAnswer: 1 pass, 1 fail",
        "check:     fail b: knownAnswer: output_differs",
        "check:     knownVectors: digest.none: 1 failed",
    ]


def test_a_check_that_compared_no_known_answer_warns(tmp_path, capsys):
    result = tmp_path / "check.yaml"
    result.write_text(yaml.safe_dump({**RESULT, "cases": [RESULT["cases"][0], RESULT["cases"][2]]}, sort_keys=False))
    check.summary(result)
    assert capsys.readouterr().out.splitlines()[-1] == (
        "warning: no_known_vector_applied: no case was compared with a known answer; list vectors in the guide entries")


def test_a_host_run_with_passes_and_a_gate_and_a_bench_that_died(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(benchmark.gradle_runner, "run", dying([{"id": "a"}]))
    document = {"run": {**DOCUMENT["run"], "passes": {"timing": {"samples": 3}}, "thermalGate": {"temperatureKeptCelsius": 36.0}}}
    problems = []
    benchmark.host_cases(OPTIONS, document, "c", "t", "e", tmp_path, tmp_path, {}, problems)
    assert capsys.readouterr().out.splitlines() == [
        "warning: run.passes: only a --device run measures in passes; this run measures once per process",
        "warning: TEMPERATURE SET BUT DEVICE CAN'T POLL: host_runtime; running without it",
        "warning: bench_failed: error: Execution failed for task ':run'",
    ]
    assert problems == ["TEMPERATURE SET BUT DEVICE CAN'T POLL: host_runtime; running without it",
                        "bench_failed: error: Execution failed for task ':run'"]


def test_a_second_hook_that_fails_to_close_is_a_warning_line(tmp_path, capsys):
    phone = Phone(tmp_path, cases=("a",))
    hooks = [Recorded(phone, "window", fails="after_process"), Recorded(phone, "clocks", fails="after_process")]
    with pytest.raises(RuntimeError, match="^clocks after_process broke$"):
        session(phone, tmp_path, hooks, [])
    lines = [line for line in capsys.readouterr().out.splitlines() if line.startswith("warning:")]
    assert lines == ["warning: hook_failed: Recorded.after_process: RuntimeError: window after_process broke"]


def test_a_failed_chart_script(tmp_path, monkeypatch, capsys):
    tools = tmp_path / "apps/benchmark-runner/analysis"
    tools.mkdir(parents=True)
    (tools / "analyze.py").write_text("import sys; print('broken input', file=sys.stderr); raise SystemExit(3)\n")
    monkeypatch.setattr(benchmark.paths, "repo", lambda: benchmark.paths.Repo(tmp_path))
    benchmark.analyse(tmp_path, {}, tmp_path / "effective.yaml", tmp_path / "preparation", tmp_path / "benchmark", [], 1)
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == f"wrote:     {tmp_path / 'benchmark/benchmark.json'}"
    assert lines[1] == "warning: charts_failed: analysis/analyze.py: broken input"
    assert lines[2].startswith("took:      analyse in ") and len(lines) == 3
