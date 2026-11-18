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
