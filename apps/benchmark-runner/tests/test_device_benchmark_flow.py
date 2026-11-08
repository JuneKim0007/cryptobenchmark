"""The device benchmark on a fake phone: processes, passes, energy windows and failures, as one shared session runs them."""
import json, pathlib, sys, types

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from device.adb import DeviceError  # noqa: E402
from session import cooldown_hook  # noqa: E402
from stages import benchmark  # noqa: E402
from fake_phone import Energy, Phone, fake_tools  # noqa: E402

OPTIONS = types.SimpleNamespace(stream=False, suppress_errors="", stacktrace=False, energy_python="python3", energy_accept_unresponsive=False)


def steps(phone):
    return [line for line in phone.log if line != "thermal"]


# The run section as :config writes it; a test overrides what it is about.
RUN = {"metrics": ["TIME"], "processRepetitions": 1, "isolation": "case", "caseCooldownSeconds": 0, "warmup": {"iterations": 0, "jobs": []}}


def layout(tmp_path, run):
    results = tmp_path / "results"
    (results / "configuration").mkdir(parents=True)
    (results / "discovery").mkdir()
    effective = results / "configuration/effective.yaml"
    effective.write_text(yaml.safe_dump({"run": {**RUN, **run}, "providers": {}}, sort_keys=False))
    capture, trial = results / "discovery/probe_1.yaml", results / "discovery/trial_1.yaml"
    capture.write_text("{}")
    trial.write_text("{}")
    return results, effective, capture, trial


def measured(tmp_path, monkeypatch, run, **phone_options):
    monkeypatch.setattr(benchmark.dependencies, "require_energy", lambda *_arguments: None)
    phone = Phone(tmp_path, **phone_options)
    fake_tools(monkeypatch, phone)
    monkeypatch.setattr(benchmark, "analyse", lambda results, files, *_rest: files.update(benchmark=results / "benchmark/benchmark.json"))
    monkeypatch.setattr(benchmark.energy_stage, "source", lambda *_arguments, **_options: Energy(phone))
    monkeypatch.setattr(benchmark.EnergySession, "pull_traces", lambda _self, _traces, fresh=True: phone.log.append("pull traces") or 0)
    results, effective, capture, trial = layout(tmp_path, run)
    files, problems = {"effective": effective}, []
    benchmark.measure_cases(OPTIONS, phone, results, results / "discovery", effective, capture, trial, files, problems)
    return phone, files, problems, results


def test_isolation_case_is_one_process_per_case_and_one_conversion(tmp_path, monkeypatch):
    phone, files, problems, results = measured(tmp_path, monkeypatch, {"isolation": "case"})
    instrumented = [s for s in steps(phone) if s.startswith("instrument ")]
    assert instrumented == ["instrument CryptoBenchmark a", "instrument CryptoBenchmark b"]
    assert steps(phone).count("convert") == 1 and steps(phone)[-1] == "convert"
    assert problems == []
    assert files["clocks"] == results / "benchmark/clocks.yaml"
    assert files["prepared"] == results / "preparation/prepared.yaml"


def test_isolation_run_is_one_process(tmp_path, monkeypatch):
    phone, _files, _problems, _results = measured(tmp_path, monkeypatch, {"isolation": "run"})
    assert [s for s in steps(phone) if s.startswith("instrument ")] == ["instrument CryptoBenchmark"]
    assert steps(phone).count("convert") == 1 and steps(phone)[-1] == "convert"


def test_repetitions_each_write_their_folder_and_merge(tmp_path, monkeypatch):
    phone, files, _problems, results = measured(tmp_path, monkeypatch, {"isolation": "case", "processRepetitions": 2})
    assert [s for s in steps(phone) if s.startswith("instrument ")] == ["instrument CryptoBenchmark a", "instrument CryptoBenchmark b"] * 2
    assert steps(phone).count("convert") == 2 and steps(phone)[-1] == "merge"
    assert files["clocks"] == [results / "benchmark/process-1/clocks.yaml", results / "benchmark/process-2/clocks.yaml"]
    assert (results / "benchmark/process-1/benchmark.json").is_file() and (results / "benchmark/process-2/benchmark.json").is_file()


def test_measured_capture_runs_inside_the_window_with_a_preflight_first(tmp_path, monkeypatch):
    phone, files, _problems, results = measured(tmp_path, monkeypatch, {"isolation": "case", "harness": {"energy": {"capture": "measured"}}})
    assert steps(phone)[:5] == ["adb push effective.yaml probe_1.yaml trial_1.yaml", "compile cryptobench", "compile test", "preflight",
                             "adb push energy.yaml"]
    assert "window open" in steps(phone) and steps(phone)[-4:] == ["pull traces", "window close", "joules", "convert"]
    assert files["energyCapability"] == results / "discovery/energy.yaml"


def test_an_energy_window_that_cannot_open_costs_the_process_its_energy_never_its_timing(tmp_path, monkeypatch):
    def refused(_self, _folder):
        raise benchmark.energy_stage.EnergyError("manafa_cannot_start: no session")
    monkeypatch.setattr(Energy, "window", refused)
    phone, _files, problems, results = measured(tmp_path, monkeypatch, {"isolation": "case", "harness": {"energy": {"capture": "measured"}}})
    assert problems == ["energy_failed: manafa_cannot_start: no session"]
    assert "joules" not in steps(phone) and "pull traces" not in steps(phone) and steps(phone)[-1] == "convert"
    assert [c["id"] for c in json.loads((results / "benchmark/benchmark.json").read_text())["cases"]] == ["a", "b"]


def test_a_crash_and_a_hang_cost_only_their_cases(tmp_path, monkeypatch):
    phone, _files, problems, _results = measured(tmp_path, monkeypatch, {"isolation": "case"}, cases=("a", "crash", "hang", "b"),
                                                 crash=("crash",), hang=("hang",))
    assert [line.split(":")[1].strip() for line in problems if line.startswith("case_failed")] == ["crash", "hang"]
    assert "force-stop" in steps(phone) and "not_measured: crash" in problems


def test_the_native_budgets_cleanups_reach_the_conversion_and_the_manifest_files(tmp_path, monkeypatch):
    cleanups = '"a": {everyCalls: 50000, cleanups: 2, pausedNanos: 900}\n'
    phone, files, _problems, results = measured(tmp_path, monkeypatch, {"isolation": "case"}, cleanups=cleanups)
    assert phone.converted[0].endswith(f" --cleanup={results / 'benchmark/native-cleanup.yaml'}")
    assert files["nativeCleanup"] == results / "benchmark/native-cleanup.yaml"
    phone, files, _problems, _results = measured(tmp_path / "none", monkeypatch, {"isolation": "case"})
    assert "--cleanup=" not in phone.converted[0] and "nativeCleanup" not in files


def test_every_case_failing_stops_the_run(tmp_path, monkeypatch):
    with pytest.raises(DeviceError, match="failed on the device for every case"):
        measured(tmp_path, monkeypatch, {"isolation": "case"}, cases=("a",), crash=("a",))


def test_each_pass_is_its_own_session_and_every_metric_comes_from_its_pass(tmp_path, monkeypatch):
    run = {"isolation": "case", "metrics": ["TIME", "ALLOCATION"], "harness": {"energy": {"capture": "measured"}},
           "passes": {"timing": {"samples": 300}, "energy": {"samples": 100}, "allocation": {"samples": 100}}}
    phone, files, _problems, results = measured(tmp_path, monkeypatch, run)
    named = [args[args.index("cryptobench.pass") + 1] + ":" + args[args.index("cryptobench.samples") + 1] for args in phone.arguments]
    assert named == ["timing:300", "timing:300", "energy:100", "energy:100", "allocation:100", "allocation:100"]
    assert steps(phone).count("window open") == 1 and steps(phone).index("window open") > steps(phone).index("instrument CryptoBenchmark b")
    assert [c.split("--metrics=")[1].split(" --thermal")[0] for c in phone.converted] == ["TIME --samples=300", "TIME --samples=100", "TIME,ALLOCATION --samples=100"]
    merged = json.loads((results / "benchmark/benchmark.json").read_text())["cases"][0]["metrics"]
    assert merged == {"timeNs": {"runs": [1.0]}, "energyJ": {"runs": [2.0]}, "allocationCount": {"runs": [3.0]}}
    assert len(files["clocks"]) == 3 and files["clocks"][0] == results / "benchmark/timing/clocks.yaml"


def test_the_throttle_sleep_reaches_every_process_and_unset_passes_nothing(tmp_path, monkeypatch):
    phone, _files, _problems, _results = measured(tmp_path, monkeypatch, {"thermalThrottleSleepSeconds": 30})
    assert all(args[args.index("androidx.benchmark.thermalThrottle.sleepDurationSeconds") + 1] == "30" for args in phone.arguments)
    phone, _files, _problems, _results = measured(tmp_path / "unset", monkeypatch, {})
    assert not any("androidx.benchmark.thermalThrottle.sleepDurationSeconds" in args for args in phone.arguments)


def test_dry_capture_is_refused_with_passes(tmp_path, monkeypatch):
    with pytest.raises(SystemExit):
        measured(tmp_path, monkeypatch, {"harness": {"energy": {"capture": "dry"}}, "passes": {"timing": {"samples": 3}}})


DUMP = """Thermal Status: 1
Cached temperatures:
\tTemperature{mValue=30.0, mType=2, mName=battery, mStatus=0}
HAL Ready: true
Current temperatures from HAL:
\tTemperature{mValue=41.5, mType=0, mName=cpu7, mStatus=1}
\tTemperature{mValue=-3.4028235E38, mType=3, mName=skin, mStatus=0}
Current cooling devices from HAL:
\tCoolingDevice{mValue=0, mType=2, mName=cpu}
"""


def test_temperature_is_read_around_every_case_and_reaches_the_conversion(tmp_path, monkeypatch):
    phone, _files, problems, results = measured(tmp_path, monkeypatch, {"isolation": "case"}, thermal=DUMP)
    assert phone.log.count("thermal") == 2 + 2 * 2
    reading = json.loads((results / "benchmark/thermal.json").read_text())
    assert reading["cases"]["a"] == {"start": {"cpu7": 41.5}, "end": {"cpu7": 41.5}, "startStatus": 1, "endStatus": 1}
    assert any("--thermal=" in converted for converted in phone.converted) and problems == []


def test_temperature_unavailable_is_null_with_a_reason_and_no_case_fails(tmp_path, monkeypatch):
    phone, _files, problems, results = measured(tmp_path, monkeypatch, {"isolation": "case"})
    reading = json.loads((results / "benchmark/thermal.json").read_text())["cases"]["b"]
    assert reading["start"] is None and reading["endStatus"] is None and reading["note"].startswith("thermal_unavailable: ")
    assert problems == [] and json.loads((results / "benchmark/benchmark.json").read_text())["cases"]


def test_one_process_for_every_case_gives_each_case_the_process_reading_noted(tmp_path, monkeypatch):
    _phone, _files, _problems, results = measured(tmp_path, monkeypatch, {"isolation": "run"}, thermal=DUMP)
    assert json.loads((results / "benchmark/thermal.json").read_text())["cases"]["a"]["note"] == "scope: run"


def test_the_warm_up_runs_once_before_the_first_pass_and_never_reaches_the_results(tmp_path, monkeypatch):
    run = {"isolation": "case", "warmup": {"iterations": 10, "jobs": [{"provider": "P", "type": "T", "name": "b"}]},
           "passes": {"timing": {"samples": 3}}}
    phone, _files, problems, results = measured(tmp_path, monkeypatch, run, cases=("a", "b"))
    log = steps(phone)
    warm = log.index("instrument CryptoBenchmark b")
    assert log[warm - 3:warm + 2] == ["list CryptoBenchmark", "pull prepared.yaml", "pull skipped.yaml", "instrument CryptoBenchmark b", "clear"]
    assert phone.arguments[0][-6:] == ("-e", "cryptobench.pass", "warmup", "-e", "cryptobench.samples", "10")
    assert sum(1 for args in phone.arguments if "warmup" in args) == 1 and problems == []
    names = [b["name"] for b in json.loads((results / "benchmark/timing/benchmarkData.json").read_text())["benchmarks"]]
    assert names == ["measure[a]", "measure[b]"]


def test_a_failed_warm_up_costs_the_run_nothing(tmp_path, monkeypatch):
    phone, _files, problems, results = measured(tmp_path, monkeypatch, {"isolation": "case", "warmup": {"iterations": 5, "jobs": []}},
                                                cases=("a", "b"), crash=("a,b",))
    assert problems == []
    assert len(json.loads((results / "benchmark/benchmark.json").read_text())["cases"]) == 2


def test_the_cool_down_sleeps_between_cases_never_before_the_first(tmp_path, monkeypatch):
    slept = []
    monkeypatch.setattr(cooldown_hook.time, "sleep", slept.append)
    measured(tmp_path, monkeypatch, {"isolation": "case", "caseCooldownSeconds": 20})
    assert slept == [20]
    measured(tmp_path / "run", monkeypatch, {"isolation": "run", "processRepetitions": 2, "caseCooldownSeconds": 5})
    assert slept == [20, 5]
    measured(tmp_path / "off", monkeypatch, {"isolation": "case"})
    assert slept == [20, 5]


def test_variants_run_interleaved_per_item_each_in_its_own_process(tmp_path, monkeypatch):
    cases = ("m_fixed", "m_notFixed", "c_fixed", "c_notFixed")
    phone, _files, _problems, _results = measured(tmp_path, monkeypatch, {"isolation": "case", "processRepetitions": 2}, cases=cases)
    run = [line.split()[-1] for line in steps(phone) if line.startswith("instrument CryptoBenchmark ")]
    assert run == ["m_fixed", "m_notFixed", "c_fixed", "c_notFixed", "m_notFixed", "m_fixed", "c_notFixed", "c_fixed"]
