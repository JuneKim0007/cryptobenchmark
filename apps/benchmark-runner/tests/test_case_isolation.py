"""isolation: case over a fake instrumentation: one case aborts its process, the others still produce results."""
import json

import pytest

from results import case_files  # noqa: E402
from session import case_isolation  # noqa: E402
from session import measure as measure_session  # noqa: E402
from fake_phone import Phone  # noqa: E402


def session(phone, tmp_path, isolation, problems=None):
    plan = measure_session.Plan("CryptoBenchmark", ("-e", "x", "y"))
    return measure_session.run_session(phone, plan, 1, isolation, [], lambda _repetition: tmp_path / "benchmark",
                                       [] if problems is None else problems)


def test_a_case_that_kills_its_process_loses_only_itself(tmp_path):
    phone, problems = Phone(tmp_path, cases=("a", "crash", "b", "hang"), crash=("crash",), hang=("hang",)), []
    process, = session(phone, tmp_path, "case", problems)
    assert [b["name"] for b in json.loads(process.data.read_text())["benchmarks"]] == ["measure[a]", "measure[b]"]
    assert [line.split(": ")[:2] for line in problems] == [["case_failed", "crash"], ["case_failed", "hang"]]
    assert "force-stop" in phone.log
    assert sorted(p.name for p in (process.into / "cases").iterdir()) == ["a.json", "b.json"]


def test_the_merged_file_is_the_one_the_kept_case_files_give_and_an_earlier_runs_files_are_gone(tmp_path):
    stale = tmp_path / "benchmark/cases/old.json"
    stale.parent.mkdir(parents=True)
    stale.write_text("{}")
    process, = session(Phone(tmp_path, cases=("a", "b")), tmp_path, "case")
    kept = [json.loads((process.into / "cases" / f"{case}.json").read_text()) for case in ("a", "b")]
    expected = {"context": kept[0]["context"], "benchmarks": [b for document in kept for b in document["benchmarks"]]}
    assert process.data.read_text() == json.dumps(expected, indent=1) and not stale.exists()


def test_isolation_run_keeps_one_process_for_every_case(tmp_path):
    phone = Phone(tmp_path, cases=("a", "b", "c", "d"))
    process, = session(phone, tmp_path, "run")
    assert phone.ran == [("CryptoBenchmark", None)]
    assert len(json.loads(process.data.read_text())["benchmarks"]) == 4


def test_the_listing_is_the_planned_cases_in_order():
    listing = "".join(f"INSTRUMENTATION_STATUS: test=measure[{case}]\n" for case in ("a", "crash", "b", "hang"))
    assert case_isolation.listed(listing + listing) == ["a", "crash", "b", "hang"]


def test_one_data_file_from_many_cases_keeps_the_first_context_in_the_order_given(tmp_path):
    case_files.cleared(tmp_path)
    for case, n in (("x", 1), ("y", 2), ("z", 3)):
        case_files.path(tmp_path, case).write_text(json.dumps({"context": {"n": n}, "benchmarks": [{"name": case}]}))
    case_files.merge(tmp_path, ["y", "x"], tmp_path / "benchmarkData.json")
    assert json.loads((tmp_path / "benchmarkData.json").read_text()) == {"context": {"n": 2}, "benchmarks": [{"name": "y"}, {"name": "x"}]}


def test_an_error_that_ends_the_session_keeps_every_case_measured_before_it(tmp_path, monkeypatch):
    phone = Phone(tmp_path, cases=("a", "b", "c"))
    cleared = phone.shell

    def offline(command):
        if command.startswith(f"rm -f {phone.data}") and ("instrument CryptoBenchmark b") in phone.log:
            raise measure_session.DeviceError("adb shell: device offline")
        return cleared(command)
    monkeypatch.setattr(phone, "shell", offline)
    with pytest.raises(measure_session.DeviceError, match="device offline"):
        session(phone, tmp_path, "case")
    data = tmp_path / "benchmark/benchmarkData.json"
    assert [b["name"] for b in json.loads(data.read_text())["benchmarks"]] == ["measure[a]", "measure[b]"]
