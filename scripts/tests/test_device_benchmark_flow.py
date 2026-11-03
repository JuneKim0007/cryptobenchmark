"""The device benchmark's steps on a fake phone, in order: what moving the loop into one shared session must keep."""
import json, pathlib, sys, types

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import pipeline  # noqa: E402
from fake_phone import Energy, Phone, fake_tools  # noqa: E402

OPTIONS = types.SimpleNamespace(stream=False, suppress_errors="", stacktrace=False, energy_python="python3", energy_accept_unresponsive=False)
CASE_PROCESS = ["clocks", "clear", "list CryptoBenchmark", "instrument CryptoBenchmark a", "pull data", "instrument CryptoBenchmark b", "pull data",
                "pull prepared.yaml", "pull skipped.yaml", "pull pins", "clocks", "convert"]


def layout(tmp_path, run):
    results = tmp_path / "results"
    (results / "configuration").mkdir(parents=True)
    (results / "discovery").mkdir()
    effective = results / "configuration/effective.yaml"
    effective.write_text(yaml.safe_dump({"run": {"metrics": ["TIME"], **run}, "providers": {}}, sort_keys=False))
    capture, trial = results / "discovery/probe_1.yaml", results / "discovery/trial_1.yaml"
    capture.write_text("{}")
    trial.write_text("{}")
    return results, effective, capture, trial


def measured(tmp_path, monkeypatch, run, **phone_options):
    phone = Phone(tmp_path, **phone_options)
    fake_tools(monkeypatch, phone)
    monkeypatch.setattr(pipeline, "analyse", lambda results, files, *_rest: files.update(benchmark=results / "benchmark/benchmark.json"))
    monkeypatch.setattr(pipeline.energy_stage, "source", lambda *_arguments, **_options: Energy(phone))
    monkeypatch.setattr(pipeline.EnergySession, "pull_traces", lambda _self, _traces: phone.log.append("pull traces") or 0)
    results, effective, capture, trial = layout(tmp_path, run)
    files, problems = {"effective": effective}, []
    pipeline.measure_cases(OPTIONS, phone, results, results / "discovery", effective, capture, trial, files, problems)
    return phone, files, problems, results


def test_isolation_case_is_one_process_per_case_and_one_conversion(tmp_path, monkeypatch):
    phone, files, problems, results = measured(tmp_path, monkeypatch, {"isolation": "case"})
    assert phone.log == ["adb push effective.yaml probe_1.yaml trial_1.yaml", "compile cryptobench", "compile test", *CASE_PROCESS]
    assert problems == []
    assert files["clocks"] == results / "benchmark/clocks.yaml"
    assert files["prepared"] == results / "preparation/prepared.yaml"


def test_isolation_run_is_one_process(tmp_path, monkeypatch):
    phone, _files, _problems, _results = measured(tmp_path, monkeypatch, {"isolation": "run"})
    assert phone.log[3:] == ["clocks", "clear", "instrument CryptoBenchmark", "pull data", "pull prepared.yaml", "pull skipped.yaml",
                             "pull pins", "clocks", "convert"]


def test_repetitions_each_write_their_folder_and_merge(tmp_path, monkeypatch):
    phone, files, _problems, results = measured(tmp_path, monkeypatch, {"isolation": "case", "processRepetitions": 2})
    assert phone.log[3:] == CASE_PROCESS + CASE_PROCESS + ["merge"]
    assert files["clocks"] == [results / "benchmark/process-1/clocks.yaml", results / "benchmark/process-2/clocks.yaml"]
    assert (results / "benchmark/process-1/benchmark.json").is_file() and (results / "benchmark/process-2/benchmark.json").is_file()


def test_measured_capture_runs_inside_the_window_with_a_preflight_first(tmp_path, monkeypatch):
    phone, files, _problems, results = measured(tmp_path, monkeypatch, {"isolation": "case", "harness": {"energy": {"capture": "measured"}}})
    assert phone.log[:5] == ["adb push effective.yaml probe_1.yaml trial_1.yaml", "compile cryptobench", "compile test", "preflight",
                             "adb push energy.yaml"]
    assert "window open" in phone.log and phone.log[-4:] == ["pull traces", "window close", "joules", "convert"]
    assert files["energyCapability"] == results / "discovery/energy.yaml"


def test_a_crash_and_a_hang_cost_only_their_cases(tmp_path, monkeypatch):
    phone, _files, problems, _results = measured(tmp_path, monkeypatch, {"isolation": "case"}, cases=("a", "crash", "hang", "b"),
                                                 crash=("crash",), hang=("hang",))
    assert [line.split(":")[1].strip() for line in problems if line.startswith("case_failed")] == ["crash", "hang"]
    assert "force-stop" in phone.log and "not_measured: crash" in problems


def test_every_case_failing_stops_the_run(tmp_path, monkeypatch):
    with pytest.raises(pipeline.DeviceError, match="failed on the device for every case"):
        measured(tmp_path, monkeypatch, {"isolation": "case"}, cases=("a",), crash=("a",))


def test_each_pass_is_its_own_session_and_every_metric_comes_from_its_pass(tmp_path, monkeypatch, capsys):
    run = {"isolation": "case", "metrics": ["TIME", "ALLOCATION"], "harness": {"energy": {"capture": "measured"}},
           "passes": {"timing": {"samples": 300}, "energy": {"samples": 100}, "allocation": {"samples": 100}}}
    phone, files, _problems, results = measured(tmp_path, monkeypatch, run)
    named = [args[args.index("cryptobench.pass") + 1] + ":" + args[args.index("cryptobench.samples") + 1] for args in phone.arguments]
    assert named == ["timing:300", "timing:300", "energy:100", "energy:100", "allocation:100", "allocation:100"]
    assert phone.log.count("window open") == 1 and phone.log.index("window open") > phone.log.index("instrument CryptoBenchmark b")
    assert [c.split("--metrics=")[1] for c in phone.converted] == ["TIME --samples=300", "TIME --samples=100", "TIME,ALLOCATION --samples=100"]
    merged = json.loads((results / "benchmark/benchmark.json").read_text())["cases"][0]["metrics"]
    assert merged == {"timeNs": {"runs": [1.0]}, "energyJ": {"runs": [2.0]}, "allocationCount": {"runs": [3.0]}}
    assert len(files["clocks"]) == 3 and files["clocks"][0] == results / "benchmark/timing/clocks.yaml"
    out = capsys.readouterr().out
    assert "pass:      timing pass: 1 process," in out and "pass:      allocation pass: 1 process," in out


def test_dry_capture_is_refused_with_passes(tmp_path, monkeypatch):
    with pytest.raises(SystemExit):
        measured(tmp_path, monkeypatch, {"harness": {"energy": {"capture": "dry"}}, "passes": {"timing": {"samples": 3}}})
