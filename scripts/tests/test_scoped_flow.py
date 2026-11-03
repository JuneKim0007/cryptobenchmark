"""The before/after run on the device session, on a fake phone: the scope check first, then the measured cases like any device case."""
import json, pathlib, sys, types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import pipeline  # noqa: E402
from fake_phone import Phone, fake_tools  # noqa: E402

OPTIONS = types.SimpleNamespace(stream=False, suppress_errors="", stacktrace=False)
CASES = ("scope:s:before", "scope:s:after", "scope:t:before", "scope:t:after")


def scoped(tmp_path, monkeypatch, run, crash=(), cooldown=0, notices=()):
    phone = Phone(tmp_path, cases=CASES, crash=crash)
    phone.notices = list(notices)
    fake_tools(monkeypatch, phone)
    files, problems = {}, []
    measuring = pipeline.Measuring(phone, None, None, OPTIONS, tmp_path / "discovery", files, problems, cooldown=cooldown)
    prepared = tmp_path / "scoped/prepared.yaml"
    prepared.parent.mkdir(parents=True)
    prepared.write_text("cases: []\n")
    pipeline.scoped_passes(measuring, {"run": {"metrics": ["TIME"], **run}}, {"none"}, prepared, CASES, tmp_path / "scoped")
    return phone, files, problems


def test_the_scope_check_is_its_own_process_before_any_case(tmp_path):
    phone = Phone(tmp_path)
    interop = phone.check_scopes(tmp_path / "scoped")
    assert phone.log == ["clear", "instrument ScopedInterop", "pull scoped-interop.yaml"] and interop.name == "scoped-interop.yaml"


def test_each_scoped_case_runs_in_its_own_process_and_a_crash_costs_only_itself(tmp_path, monkeypatch):
    phone, files, problems = scoped(tmp_path, monkeypatch, {"isolation": "case", "scopedRepetitions": 1}, crash=("scope:t:before",))
    assert [named for _class, named in phone.ran] == list(CASES)
    assert problems == ["case_failed: scope:t:before: INSTRUMENTATION_RESULT: shortMsg=Process crashed."]
    assert [c["id"] for c in json.loads(files["scoped"].read_text())["cases"]] == ["scope:s:before", "scope:s:after", "scope:t:after"]
    assert files["clocks"] == tmp_path / "scoped/clocks.yaml"


def test_three_repetitions_by_default_alternate_before_and_after_and_merge(tmp_path, monkeypatch):
    phone, files, _problems = scoped(tmp_path, monkeypatch, {"isolation": "case", "processRepetitions": 1})
    s_sides = [named.rsplit(":", 1)[1] for _class, named in phone.ran if named.startswith("scope:s:")]
    assert s_sides == ["before", "after", "after", "before", "before", "after"] and phone.log[-1] == "merge"
    assert files["processes"] == [tmp_path / f"scoped/process-{n}/benchmark.json" for n in (1, 2, 3)]
    assert len(json.loads(files["scoped"].read_text())["cases"][0]["metrics"]["timeNs"]["runs"]) == 3


def test_one_process_for_every_scoped_case_names_them_in_order(tmp_path, monkeypatch):
    phone, _files, _problems = scoped(tmp_path, monkeypatch, {"isolation": "run", "scopedRepetitions": 2})
    assert phone.ran == [("ScopedBenchmark", ",".join(CASES)),
                         ("ScopedBenchmark", "scope:s:after,scope:s:before,scope:t:after,scope:t:before")]


def test_the_cool_down_sleeps_between_scoped_cases_too(tmp_path, monkeypatch):
    slept = []
    monkeypatch.setattr(pipeline.cooldown_hook.time, "sleep", slept.append)
    scoped(tmp_path, monkeypatch, {"isolation": "case", "scopedRepetitions": 1}, cooldown=10)
    assert slept == [10, 10, 10]


def test_a_case_short_of_its_samples_is_recorded_as_a_problem(tmp_path, monkeypatch):
    short = "iterations_not_applied: scope:s:before asked for 100, timeNs has 50 runs"
    _phone, _files, problems = scoped(tmp_path, monkeypatch, {"isolation": "run", "scopedRepetitions": 1}, notices=(short, "warning: other"))
    assert problems == [short]
