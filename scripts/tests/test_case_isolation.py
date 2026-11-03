"""isolation: case over a fake instrumentation: one case aborts its process, the others still produce results."""
import json, pathlib, sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import case_isolation, measure_session  # noqa: E402
import device as device_module  # noqa: E402
from fake_phone import Phone  # noqa: E402


def session(phone, tmp_path, isolation, problems=None):
    plan = measure_session.Plan("CryptoBenchmark", ("-e", "x", "y"))
    return measure_session.run_session(phone, plan, 1, isolation, [], lambda _repetition: tmp_path / "benchmark",
                                       [] if problems is None else problems)


def test_a_case_that_kills_its_process_loses_only_itself(tmp_path, capsys):
    phone, problems = Phone(tmp_path, cases=("a", "crash", "b", "hang"), crash=("crash",), hang=("hang",)), []
    process, = session(phone, tmp_path, "case", problems)
    assert [b["name"] for b in json.loads(process.data.read_text())["benchmarks"]] == ["measure[a]", "measure[b]"]
    assert problems == ["case_failed: crash: INSTRUMENTATION_RESULT: shortMsg=Process crashed.",
                        "case_failed: hang: timeout: case ran past 3600 s: adb shell am instrument"]
    assert "force-stop" in phone.log
    out = capsys.readouterr().out
    assert "measure:   one process per case (4 cases, isolation: case)" in out and out.count("case_failed: ") == 2
    assert not list(process.into.glob(".*.json"))


def test_every_case_failing_is_the_runs_failure(tmp_path):
    with pytest.raises(device_module.DeviceError, match="CryptoBenchmark failed on the device for every case:"):
        session(Phone(tmp_path, cases=("a",), crash=("a",)), tmp_path, "case")


def test_isolation_run_keeps_one_process_for_every_case(tmp_path, capsys):
    phone = Phone(tmp_path, cases=("a", "b", "c", "d"))
    process, = session(phone, tmp_path, "run")
    assert phone.ran == [("CryptoBenchmark", None)]
    assert len(json.loads(process.data.read_text())["benchmarks"]) == 4
    assert "measure:   one process for every case (isolation: run)" in capsys.readouterr().out


def test_the_listing_is_the_planned_cases_in_order():
    listing = "".join(f"INSTRUMENTATION_STATUS: test=measure[{case}]\n" for case in ("a", "crash", "b", "hang"))
    assert case_isolation.listed(listing + listing) == ["a", "crash", "b", "hang"]


def test_one_data_file_from_many_processes_keeps_the_first_context():
    documents = [{"context": {"n": 1}, "benchmarks": [{"name": "x"}]}, {"context": {"n": 2}, "benchmarks": [{"name": "y"}]}]
    assert case_isolation.merged(documents) == {"context": {"n": 1}, "benchmarks": [{"name": "x"}, {"name": "y"}]}
