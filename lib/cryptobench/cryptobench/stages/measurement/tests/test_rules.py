"""The rules table: check_case's rows on a pulled file, and the launch loop acting on them (rejected/, relaunched, retries)."""
import json
import types

import pytest
import yaml

from cryptobench.stages.measurement.session import case_isolation, dynamic_temperature  # noqa: E402
from cryptobench.stages.measurement.session import launch as launch_module, measure  # noqa: E402
from cryptobench.stages.measurement.validation import expectation, rules  # noqa: E402

SINGLE = expectation.Expectation(None, None)


def data(path, repeat=70_000, ns=1600.0, warmup=1000, runs=3, name="measure[a]"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"benchmarks": [{"name": name, "repeatIterations": repeat, "warmupIterations": warmup,
                                                "metrics": {"timeNs": {"runs": [ns] * runs}}}]}))
    return path


def codes(path, expected=SINGLE, samples=None):
    return [(f.code, f.severity) for f in rules.check_case(rules.Result("process-1", "a", path, samples), expected)]


def test_a_good_file_has_no_finding(tmp_path):
    assert codes(data(tmp_path / "a.json")) == []


def test_no_file_is_no_data_and_nothing_after_it(tmp_path):
    assert codes(tmp_path / "a.json") == [("no_data", "fail")]


@pytest.mark.parametrize("name", ["measure[b]", "EMULATOR_measure[b]"])
def test_another_case_is_result_mismatch_and_a_prefix_androidx_adds_still_names_it(tmp_path, name):
    assert codes(data(tmp_path / "a.json", name=name)) == [("result_mismatch", "fail")]
    assert codes(data(tmp_path / "a.json", name="DEBUGGABLE_EMULATOR_measure[a]")) == []


def test_a_collapsed_sample_is_miscalibrated(tmp_path):
    [finding] = rules.check_case(rules.Result("process-1", "a", data(tmp_path / "a.json", repeat=1, ns=38_000.0)), SINGLE)
    assert (finding.code, finding.detail) == ("miscalibrated", "measure[a]: 1 calls per sample, 0.038 ms a sample")


def test_a_warmup_near_the_cap_is_a_note_only_when_the_samples_are_usable(tmp_path):
    assert codes(data(tmp_path / "a.json", warmup=4_500_000)) == [("warmup_near_cap", "note")]
    assert codes(data(tmp_path / "a.json", repeat=1, ns=38_000.0, warmup=4_500_000)) == [("miscalibrated", "fail")]


def test_sample_count_is_the_passes_samples_or_a_relaunchs_and_unchecked_when_nothing_says(tmp_path):
    timing = expectation.Expectation("timing", 3)
    assert codes(data(tmp_path / "a.json", runs=3), timing) == []
    assert codes(data(tmp_path / "a.json", runs=2), timing) == [("sample_count", "fail")]
    assert codes(data(tmp_path / "a.json", runs=38), expectation.Expectation("energy", 10, 5), samples=38) == []
    assert codes(data(tmp_path / "a.json", runs=7), SINGLE) == []


def test_the_single_pass_expects_each_cases_own_iterations_from_prepared_yaml(tmp_path):
    prepared = tmp_path / "prepared.yaml"
    prepared.write_text(yaml.safe_dump({"cases": [{"id": "a", "harness": {"iterations": 4}}, {"id": "b"}]}))
    planned = SINGLE.planned(prepared)
    assert planned.iterations == {"a": 4} and codes(data(tmp_path / "a.json", runs=3), planned) == [("sample_count", "fail")]
    assert expectation.Expectation("timing", 3).planned(prepared).iterations == {}


def test_of_reads_the_record_run_block():
    run = {"passes": {"timing": {"samples": 3}, "energy": {"samples": 10, "minWindowSeconds": 5}}}
    assert expectation.of(run, "energy") == expectation.Expectation("energy", 10, 5)
    assert expectation.of(run, None) == SINGLE


def launches(monkeypatch, tmp_path, repeats, retries=2):
    unit = tmp_path / "unit"
    into = unit / "benchmark"
    file = into / "cases/a.json"
    calls = []

    def launch(_device, _test, _arguments, _case, pulled):
        calls.append(1)
        data(pulled, repeat=repeats[len(calls) - 1])
    monkeypatch.setattr(case_isolation, "launch_case", launch)
    plan = types.SimpleNamespace(gate=dynamic_temperature.Off(), retries=retries, test_class="T", arguments=(), sizing=None, unit=unit, expectation=SINGLE)
    process = measure.Process(1, into)
    return launch_module.run_of_case(None, plan, process, "a", [], file), len(calls), process, unit


def test_a_collapsed_launch_is_rejected_measured_again_and_kept_if_the_second_is_good(monkeypatch, tmp_path):
    outcome, count, process, unit = launches(monkeypatch, tmp_path, [1, 70_000])
    assert (outcome, count) == (None, 2) and process.relaunched == [{"case": "a", "attempt": 1, "code": "miscalibrated"}]
    [rejected] = (unit / "rejected").iterdir()
    assert sorted(p.name for p in (rejected / "process-1").iterdir()) == ["a.json", "why.yaml"]
    why = yaml.safe_load((rejected / "process-1/why.yaml").read_text())
    assert (why["case"], why["attempt"], why["run"], why["findings"][0]["code"]) == ("a", 1, "process-1", "miscalibrated")
    assert json.loads((unit / "benchmark/cases/a.json").read_text())["benchmarks"][0]["repeatIterations"] == 70_000


def test_a_launch_collapsed_three_times_fails_the_case_and_every_attempt_is_kept(monkeypatch, tmp_path):
    failure, count, process, unit = launches(monkeypatch, tmp_path, [1, 1, 1])
    assert count == 3 and failure.startswith("case_failed: a: miscalibrated: measure[a]: 1 calls")
    assert len(list((unit / "rejected").iterdir())) == 3 and [r["attempt"] for r in process.relaunched] == [1, 2]
    assert not (unit / "benchmark/cases/a.json").exists()


def test_a_good_launch_runs_once(monkeypatch, tmp_path):
    outcome, count, process, unit = launches(monkeypatch, tmp_path, [70_000])
    assert (outcome, count, process.relaunched) == (None, 1, []) and not (unit / "rejected").exists()


def run_folder(tmp_path, order, files, problems=(), record=None):
    into = tmp_path / "benchmark"
    (into / "cases").mkdir(parents=True)
    (into / "order.txt").write_text("".join(f"{case}\n" for case in order))
    for case in files:
        data(into / "cases" / f"{case}.json", name=f"measure[{case}]")
    return rules.RunFolder(tmp_path, into, into, 1, tuple(problems), record)


def test_check_run_names_a_missing_case_but_not_one_the_run_gave_up_on_and_notes_an_extra_file(tmp_path):
    run = run_folder(tmp_path, ["a", "b", "c"], ["a", "x"], ["case_failed: b: Process crashed."])
    found = [(f.code, f.case, f.severity, f.run) for f in rules.check_run(run, SINGLE)]
    assert found == [("case_missing", "c", "fail", "process-1"), ("case_extra", "x", "note", "process-1")]
    assert rules.redone(rules.check_run(run, SINGLE)) == ["c"]


def test_files_match_record_names_the_case_whose_file_changed_and_a_run_file(tmp_path):
    from cryptobench.stages.measurement.session import blocks
    run = run_folder(tmp_path, ["a", "b"], ["a", "b"])
    recorded = blocks.run_files(run.folder, run.folder)
    (run.folder / "cases/b.json").write_text((run.folder / "cases/b.json").read_text() + " ")
    (run.folder / "order.txt").write_text("a\nb\n\n")
    found = rules.check_run(rules.RunFolder(tmp_path, run.folder, run.folder, 1, (), recorded), SINGLE)
    assert [(f.code, f.case, f.detail) for f in found] == [("files_differ", "b", "cases/b.json: its digest differs"),
                                                           ("files_differ", None, "order.txt: its digest differs")]


def test_a_relaunch_counts_the_samples_it_asked_for(tmp_path):
    run = run_folder(tmp_path, ["a"], [])
    data(run.folder / "cases/a.json", runs=75)
    energy = expectation.Expectation("energy", 3, 5)
    assert [f.code for f in rules.check_run(run, energy)] == ["sample_count"]
    sized = rules.RunFolder(tmp_path, run.folder, run.folder, 1, sized={"a": {"samples": 3, "relaunched": {"samples": 75}}})
    assert rules.check_run(sized, energy) == []


def test_the_energy_pass_rows_note_a_kept_short_window_and_an_uncovered_window(tmp_path):
    run = run_folder(tmp_path, ["a", "b"], ["a", "b"])
    (run.folder / "energy-samples.yaml").write_text(yaml.safe_dump({"cases": {"a": {"samples": 3, "windowSeconds": 1.0, "shortWindow": True}}}))
    (run.folder / "energy.json").write_text(json.dumps({"cases": {"b": {"valid": False, "invalid": ["window_uncovered"]}}}))
    found = [(f.code, f.scope, f.case, f.severity) for f in rules.check_run(run, expectation.Expectation("energy", 3, 5))]
    assert found == [("short_window", "pass", "a", "note"), ("window_uncovered", "pass", "b", "note")]
    assert rules.check_run(run, expectation.Expectation("timing", 3)) == []


def test_a_host_process_folder_without_case_files_is_held_only_against_its_record_even_beside_its_order(tmp_path):
    into = tmp_path / "benchmark/process-1"
    into.mkdir(parents=True)
    (into / "benchmark.json").write_text("{}")
    from cryptobench.stages.measurement.session import blocks
    for files in ((), ("order.txt",)):
        for name in files:
            (into / name).write_text("a\nb\n")
        run = rules.RunFolder(tmp_path, into, into.parent, 1, (), blocks.run_files(into, into.parent))
        assert (run.order, rules.check_run(run, SINGLE)) == (None, [])
