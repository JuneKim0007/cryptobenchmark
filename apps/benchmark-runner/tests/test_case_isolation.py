"""isolation: case over a fake instrumentation: one case aborts its process, the others still produce results."""
import json, pathlib, re, sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from results import case_files  # noqa: E402
from session import case_isolation  # noqa: E402
from session import measure as measure_session  # noqa: E402
from device import adb as device_module  # noqa: E402
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
    assert [line for line in out.splitlines() if line.startswith("case:")] == [
        "case:      1 of 4 a ok", "case:      2 of 4 crash failed", "case:      3 of 4 b ok", "case:      4 of 4 hang failed"]
    assert sorted(p.name for p in (process.into / "cases").iterdir()) == ["a.json", "b.json"]


def test_the_merged_file_is_the_one_the_kept_case_files_give_and_an_earlier_runs_files_are_gone(tmp_path):
    stale = tmp_path / "benchmark/cases/old.json"
    stale.parent.mkdir(parents=True)
    stale.write_text("{}")
    process, = session(Phone(tmp_path, cases=("a", "b")), tmp_path, "case")
    kept = [json.loads((process.into / "cases" / f"{case}.json").read_text()) for case in ("a", "b")]
    expected = {"context": kept[0]["context"], "benchmarks": [b for document in kept for b in document["benchmarks"]]}
    assert process.data.read_text() == json.dumps(expected, indent=1) and not stale.exists()


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


def test_one_data_file_from_many_cases_keeps_the_first_context_in_the_order_given(tmp_path):
    case_files.cleared(tmp_path)
    for case, n in (("x", 1), ("y", 2), ("z", 3)):
        case_files.path(tmp_path, case).write_text(json.dumps({"context": {"n": n}, "benchmarks": [{"name": case}]}))
    case_files.merge(tmp_path, ["y", "x"], tmp_path / "benchmarkData.json")
    assert json.loads((tmp_path / "benchmarkData.json").read_text()) == {"context": {"n": 2}, "benchmarks": [{"name": "y"}, {"name": "x"}]}


def test_only_case_files_builds_the_cases_path():
    scripts = pathlib.Path(__file__).resolve().parent.parent
    built = re.compile(r"""/\s*f?["']cases["'/]|["']cases/|=\s*["']cases["']\s*$""", re.MULTILINE)
    owners = [p.relative_to(scripts).as_posix() for p in sorted(scripts.rglob("*.py"))
              if "tests" not in p.parts and built.search(p.read_text())]
    assert owners == ["results/case_files.py"]
