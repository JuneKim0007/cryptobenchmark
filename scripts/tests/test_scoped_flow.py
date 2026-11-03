"""The before/after run on the device session, on a fake phone: the scope check first, then the measured cases like any device case."""
import json, pathlib, sys, types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import pipeline  # noqa: E402
from fake_phone import Phone, fake_tools  # noqa: E402

OPTIONS = types.SimpleNamespace(stream=False, suppress_errors="", stacktrace=False)
CASES = ("scope:s:before", "scope:s:after", "scope:t:before", "scope:t:after")


def scoped(tmp_path, monkeypatch, run, crash=()):
    phone = Phone(tmp_path, cases=CASES, crash=crash)
    fake_tools(monkeypatch, phone)
    files, problems = {}, []
    measuring = pipeline.Measuring(phone, None, None, OPTIONS, tmp_path / "discovery", files, problems)
    prepared = tmp_path / "scoped/prepared.yaml"
    prepared.parent.mkdir(parents=True)
    prepared.write_text("cases: []\n")
    pipeline.measure_scoped(measuring, {"none"}, ["TIME"], prepared, CASES, {"run": {"metrics": ["TIME"], **run}}, tmp_path / "scoped")
    return phone, files, problems


def test_the_scope_check_is_its_own_process_before_any_case(tmp_path):
    phone = Phone(tmp_path)
    interop = phone.check_scopes(tmp_path / "scoped")
    assert phone.log == ["clear", "instrument ScopedInterop", "pull scoped-interop.yaml"] and interop.name == "scoped-interop.yaml"


def test_each_scoped_case_runs_in_its_own_process_and_a_crash_costs_only_itself(tmp_path, monkeypatch):
    phone, files, problems = scoped(tmp_path, monkeypatch, {"isolation": "case"}, crash=("scope:t:before",))
    assert [named for _class, named in phone.ran] == list(CASES)
    assert problems == ["case_failed: scope:t:before: INSTRUMENTATION_RESULT: shortMsg=Process crashed."]
    assert [c["id"] for c in json.loads(files["scoped"].read_text())["cases"]] == ["scope:s:before", "scope:s:after", "scope:t:after"]
    assert files["clocks"] == tmp_path / "scoped/clocks.yaml"


def test_repetitions_merge_and_record_every_process(tmp_path, monkeypatch):
    phone, files, _problems = scoped(tmp_path, monkeypatch, {"isolation": "case", "processRepetitions": 3})
    assert len(phone.ran) == 12 and phone.log[-1] == "merge"
    assert files["processes"] == [tmp_path / f"scoped/process-{n}/benchmark.json" for n in (1, 2, 3)]
    assert len(json.loads(files["scoped"].read_text())["cases"][0]["metrics"]["timeNs"]["runs"]) == 3


def test_one_process_for_every_scoped_case_names_them_in_order(tmp_path, monkeypatch):
    phone, _files, _problems = scoped(tmp_path, monkeypatch, {"isolation": "run"})
    assert phone.ran == [("ScopedBenchmark", ",".join(CASES))]
