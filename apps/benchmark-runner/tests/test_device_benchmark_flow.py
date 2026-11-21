"""The device benchmark on a fake phone: processes, passes, energy windows and failures, as one shared session runs them."""
import json, pathlib, types

import pytest
import yaml

from cryptobench.shared.device.adb import DeviceError  # noqa: E402
from cryptobench.shared.errors.failures import EnergyError  # noqa: E402
from cryptobench.shared.device import reconnect  # noqa: E402
from cryptobench.stages.measurement.session import clocks_hook, cooldown_hook, dynamic_temperature, variant_order  # noqa: E402
import pipeline  # noqa: E402
from cryptobench.stages.measurement import benchmark, resume  # noqa: E402
from cryptobench.stages.discovery import discover  # noqa: E402
from cryptobench.stages.measurement.session import blocks, skips  # noqa: E402
from failure import reported  # noqa: E402
from fake_phone import MISSING, NOT_PREPARED, OK, PROBE, Energy, Phone, fake_tools, jetpack_case  # noqa: E402

OPTIONS = types.SimpleNamespace(stream=False, suppress_errors="", stacktrace=False, energy_python="python3", energy_accept_unresponsive=False,
                                reconnect_wait_minutes=None, reconnect_poll_seconds=None)


def steps(phone):
    return [line for line in phone.log if line != "thermal"]


# The run section as :config writes it; a test overrides what it is about. Seed 4792 draws the listed order for these fixtures' few cases.
RUN = {"inputSizes": [1024], "phases": ["WARM"], "metrics": ["TIME"], "variants": ["fixed", "notFixed", "secure"], "processRepetitions": 1, "seed": 0,
       "caseCooldownSeconds": 0, "launchRetries": 0, "energyIdleSeconds": 120, "resumeBlockRuns": 10, "orderSeed": 4792, "warmup": {"iterations": 0, "jobs": [], "cases": 3}}


def layout(tmp_path, run, providers=None):
    results = tmp_path / "results"
    (results / "configuration").mkdir(parents=True)
    (results / "discovery").mkdir()
    effective = results / "configuration/effective.yaml"
    effective.write_text(yaml.safe_dump({"run": {**RUN, **run}, "providers": providers or {}}, sort_keys=False))
    capture, trial = results / "discovery/probe_1.yaml", results / "discovery/trial_1.yaml"
    capture.write_text(yaml.safe_dump(PROBE))
    trial.write_text("{}")
    return results, effective, capture, trial


def measured_fakes(monkeypatch, phone):
    """The host tools, analysis and energy source a measuring run calls, faked around the phone."""
    monkeypatch.setattr(pipeline.dependencies, "require_energy", lambda *_arguments: None)
    fake_tools(monkeypatch, phone)
    monkeypatch.setattr(pipeline, "analyse", lambda results, files, *_rest: files.update(benchmark=results / "benchmark/benchmark.json"))
    monkeypatch.setattr(benchmark.energy_stage, "source", lambda *_arguments, **_options: Energy(phone))
    monkeypatch.setattr(benchmark.EnergySession, "pull_traces", lambda _self, _traces, fresh=True: phone.log.append("pull traces") or 0)


def measured(tmp_path, monkeypatch, run, phone=None, providers=None, **phone_options):
    phone = phone or Phone(tmp_path, **phone_options)
    measured_fakes(monkeypatch, phone)
    results, effective, capture, trial = layout(tmp_path, run, providers)
    files, problems = {"effective": effective}, []
    pipeline.benchmarked(OPTIONS, phone, results, discover.Discovered(results / "discovery", effective, capture, trial, files), problems,
                         {"identity": "of this run", "run": yaml.safe_load(effective.read_text())["run"]}, resume.NOTHING)
    return phone, files, problems, results


def test_one_process_per_case_and_one_conversion(tmp_path, monkeypatch):
    phone, files, problems, results = measured(tmp_path, monkeypatch, {})
    instrumented = [s for s in steps(phone) if s.startswith("instrument ")]
    assert instrumented == ["instrument CryptoBenchmark a", "instrument CryptoBenchmark b"]
    assert steps(phone).count("convert") == 1 and steps(phone)[-1] == "convert"
    assert problems == []
    assert files["clocks"] == results / "benchmark/clocks.yaml"
    assert files["prepared"] == results / "preparation/prepared.yaml"


def test_repetitions_each_write_their_folder_and_merge(tmp_path, monkeypatch):
    phone, files, _problems, results = measured(tmp_path, monkeypatch, {"processRepetitions": 2})
    assert [s for s in steps(phone) if s.startswith("instrument ")] == ["instrument CryptoBenchmark a", "instrument CryptoBenchmark b"] * 2
    assert steps(phone).count("convert") == 2 and steps(phone)[-1] == "merge"
    assert files["clocks"] == [results / "benchmark/process-1/clocks.yaml", results / "benchmark/process-2/clocks.yaml"]
    assert (results / "benchmark/process-1/benchmark.json").is_file() and (results / "benchmark/process-2/benchmark.json").is_file()


MEASURED = {"harness": {"energy": {"capture": "measured"}}, "passes": {"energy": {"samples": 3, "minWindowSeconds": 5}, "timing": {"samples": 3}}}


def test_measured_capture_runs_inside_the_window_with_a_preflight_first(tmp_path, monkeypatch):
    phone, files, _problems, results = measured(tmp_path, monkeypatch, MEASURED)
    assert steps(phone)[:5] == ["adb push effective.yaml guide.yaml probe_1.yaml trial_1.yaml", "compile cryptobench", "compile test", "preflight",
                             "adb push energy.yaml"]
    closing = len(steps(phone)) - 1 - steps(phone)[::-1].index("pull traces")
    assert "window open" in steps(phone) and steps(phone)[closing:closing + 4] == ["pull traces", "window close", "joules", "convert"]
    assert files["energyCapability"] == results / "discovery/energy.yaml"


def test_the_end_idle_reading_follows_the_last_pass_and_each_process_reads_its_energy_again(tmp_path, monkeypatch):
    phone, _files, problems, _results = measured(tmp_path, monkeypatch, MEASURED | {"processRepetitions": 2})
    tail = steps(phone)[steps(phone).index("idle end"):]
    assert tail == ["idle end", "joules", "convert", "joules", "convert", "merge"] + ["merge passes"] * 3
    assert steps(phone).index("idle end") > max(i for i, s in enumerate(steps(phone)) if s.startswith("instrument "))
    assert problems == []


def test_the_block_records_follow_the_energy_files_the_end_idle_rewrote(tmp_path, monkeypatch):
    written = []

    def joules(self, *paths):
        self.phone.log.append("joules")
        written.append(paths[-1])
        paths[-1].write_text(json.dumps({"call": len(written)}))
    monkeypatch.setattr(Energy, "joules", joules)
    _phone, _files, problems, results = measured(tmp_path, monkeypatch, MEASURED | {"processRepetitions": 2})
    folder = results / "benchmark/energy"
    runs = [run for record in blocks.recorded(folder).values() for run in record["processes"]]
    assert len(written) == 4 and len(runs) == 2 and problems == []
    assert all(run["files"] == blocks.run_files(folder / run["folder"], folder) for run in runs)


def test_an_end_idle_reading_that_fails_keeps_the_start_reading_and_says_so(tmp_path, monkeypatch):
    def failed(_self, _session, _discovery, _held):
        raise EnergyError("apps/benchmark-runner/energy/preflight.py: no_rails: the end idle trace has no power rails")
    monkeypatch.setattr(Energy, "idle_end", failed)
    phone, _files, problems, _results = measured(tmp_path, monkeypatch, MEASURED)
    assert problems == ["energy_failed: the end idle reading: apps/benchmark-runner/energy/preflight.py: no_rails: the end idle trace has no power rails",
                        "idle_start_only: no end idle reading; energy.json keeps the start reading alone"]
    assert steps(phone).count("joules") == 1


@pytest.mark.parametrize("lost", [reconnect.DeviceGone("adb: device offline; not back after 3600 s; phase stopped"),
                                  dynamic_temperature.Terminated("temperature_gate_timeout: the end idle reading: energy idle: still above")])
def test_a_device_lost_before_the_end_reading_keeps_every_process_on_the_start_reading(tmp_path, monkeypatch, lost):
    def gone(_self, _session, _discovery, _held):
        raise lost
    monkeypatch.setattr(Energy, "idle_end", gone)
    phone, _files, problems, results = measured(tmp_path, monkeypatch, MEASURED | {"processRepetitions": 2})
    assert problems == [f"energy_failed: the end idle reading: {lost}", "idle_start_only: no end idle reading; energy.json keeps the start reading alone"]
    assert steps(phone).count("joules") == 2 and steps(phone)[-3:] == ["merge passes"] * 3
    for process in (1, 2):
        assert (results / f"benchmark/energy/process-{process}/energy.json").is_file()
    assert (results / "benchmark/benchmark.json").is_file()


def test_a_conversion_that_fails_mid_redo_leaves_every_process_as_the_start_reading_wrote_it(tmp_path, monkeypatch):
    phone = Phone(tmp_path)
    phone.convert_fails = lambda words: "energy-redo" in words[2] and "process-2" in words[2]
    before = {}

    def idle_end(self, _session, _discovery, held):
        held(lambda: None)
        for process in (1, 2):
            folder = tmp_path / f"results/benchmark/energy/process-{process}"
            before[process] = ((folder / "energy.json").read_text(), (folder / "benchmark.json").read_text())
        return True
    monkeypatch.setattr(Energy, "idle_end", idle_end)
    phone, _files, problems, results = measured(tmp_path, monkeypatch, MEASURED | {"processRepetitions": 2}, phone=phone)
    assert problems == ["energy_failed: energy again: nothing_converted: no benchmark gave a row",
                        "idle_start_only: energy again failed; every energy.json keeps the start reading alone"]
    assert steps(phone)[steps(phone).index("convert failed") - 3:][:4] == ["joules", "convert", "joules", "convert failed"]
    for process in (1, 2):
        folder = results / f"benchmark/energy/process-{process}"
        assert ((folder / "energy.json").read_text(), (folder / "benchmark.json").read_text()) == before[process]
        assert not (folder / "energy-redo").exists()


def test_a_redo_that_succeeds_swaps_in_every_staged_file_and_clears_the_staging(tmp_path, monkeypatch):
    phone, _files, problems, results = measured(tmp_path, monkeypatch, MEASURED | {"processRepetitions": 2})
    assert problems == [] and phone.energy.skins == [{"start": None, "end": None}] * 2
    written = [json.loads((results / f"benchmark/energy/process-{p}/energy.json").read_text())["written"] for p in (1, 2)]
    assert written == [3, 4]
    assert not any(results.rglob("energy-redo"))


def test_a_source_that_subtracts_no_idle_takes_no_end_reading(tmp_path, monkeypatch):
    monkeypatch.setattr(Energy, "idle_end", lambda _self, _session, _discovery, _held: False)
    phone, _files, problems, _results = measured(tmp_path, monkeypatch, MEASURED)
    assert steps(phone).count("joules") == 1 and problems == []


def test_a_run_without_energy_takes_no_idle_reading(tmp_path, monkeypatch):
    phone, _files, _problems, _results = measured(tmp_path, monkeypatch, {})
    assert "preflight" not in steps(phone) and "idle end" not in steps(phone)


def test_an_energy_window_that_cannot_open_costs_the_process_its_energy_never_its_timing(tmp_path, monkeypatch):
    def refused(_self, _folder):
        raise EnergyError("manafa_cannot_start: no session")
    monkeypatch.setattr(Energy, "window", refused)
    phone, _files, problems, results = measured(tmp_path, monkeypatch, MEASURED)
    assert problems == ["energy_failed: manafa_cannot_start: no session"]
    assert "joules" not in steps(phone) and "pull traces" not in steps(phone) and steps(phone)[-1] == "merge passes"
    assert [c["id"] for c in json.loads((results / "benchmark/benchmark.json").read_text())["cases"]] == ["a", "b"]


def test_a_clock_read_that_fails_before_the_process_closes_the_open_energy_window(tmp_path, monkeypatch):
    def unreadable(_device):
        raise DeviceError("adb shell: device offline")
    monkeypatch.setattr(clocks_hook.clocks, "read", unreadable)
    phone = Phone(tmp_path)
    with pytest.raises(DeviceError, match="device offline"):
        measured(tmp_path, monkeypatch, MEASURED, phone=phone)
    assert steps(phone)[-5:] == ["window open", "window close", "pull prepared.yaml", "pull skipped.yaml", "pull pins"]


def test_a_clock_record_that_fails_after_the_process_still_closes_the_window_and_converts(tmp_path, monkeypatch):
    def unwritable(*_arguments):
        raise OSError("clocks.yaml: no space left")
    monkeypatch.setattr(clocks_hook.clocks, "write", unwritable)
    phone = Phone(tmp_path)
    with pytest.raises(OSError, match="no space left"):
        measured(tmp_path, monkeypatch, MEASURED, phone=phone)
    assert steps(phone)[-4:] == ["pull traces", "window close", "joules", "convert"]
    assert [c["id"] for c in json.loads((tmp_path / "results/benchmark/energy/benchmark.json").read_text())["cases"]] == ["a", "b"]


def test_a_crash_and_a_hang_cost_only_their_cases(tmp_path, monkeypatch):
    phone, _files, problems, _results = measured(tmp_path, monkeypatch, {}, cases=("a", "crash", "hang", "b"),
                                                 crash=("crash",), hang=("hang",))
    assert [line.split(":")[1].strip() for line in problems if line.startswith("case_failed")] == ["crash", "hang"]
    assert "force-stop" in steps(phone) and "not_measured: crash" in problems


# a Pixel 10's StrongBox refusals as its skipped.yaml recorded them, each case three times (one launch and launchRetries 2)
STRONGBOX = yaml.safe_load((pathlib.Path(__file__).parent / "fixtures/skipped_strongbox.yaml").read_text())
REFUSED = {record["caseId"]: record for record in STRONGBOX["skipped"]}


def test_every_strongbox_refusal_on_record_is_a_final_keystore_unsupported_skip():
    assert skips.recorded(STRONGBOX) == {case: "keystore_unsupported" for case in REFUSED} and len(REFUSED) == 5
    assert skips.coded({"caseId": "x", "code": "hook_failed_somewhere"}) is None and skips.coded({"code": "provider_not_installed"}) is None
    assert skips.coded({"caseId": "x", "code": "bench_failed", "reason": "a notice is no skip"}) is None


def test_a_skipped_yaml_of_the_old_schema_is_refused():
    with pytest.raises(Exception, match="unsupported_schema_version: skipped.yaml: 1, this build reads 2"):
        skips.recorded({"schemaVersion": 1, "skipped": []})


def test_a_coded_preparation_skip_is_final_and_a_crash_keeps_its_retries(tmp_path, monkeypatch):
    refused = next(iter(REFUSED))
    phone, _files, problems, _results = measured(tmp_path, monkeypatch, {"launchRetries": 2},
                                                 cases=("a", "crash", refused, "b"), crash=("crash",), refuse=REFUSED)
    launched = [s for s in steps(phone) if s.startswith("instrument ")]
    assert launched.count(f"instrument CryptoBenchmark {refused}") == 1 and launched.count("instrument CryptoBenchmark crash") == 3
    assert f"case_skipped: {refused}: keystore_unsupported" in problems and not any(line.startswith(f"case_failed: {refused}") for line in problems)


def test_a_process_whose_every_case_is_a_coded_skip_is_an_outcome_not_a_device_error(tmp_path, monkeypatch):
    phone, files, problems, _results = measured(tmp_path, monkeypatch, {"launchRetries": 2}, cases=tuple(REFUSED), refuse=REFUSED)
    launched = variant_order.shuffled(RUN["orderSeed"])(1, list(REFUSED))
    assert [s for s in steps(phone) if s.startswith("instrument ")] == [f"instrument CryptoBenchmark {case}" for case in launched]
    assert problems[:-1] == [f"case_skipped: {case}: keystore_unsupported" for case in launched]
    assert problems[-1].startswith("all_cases_skipped: every case of CryptoBenchmark is a coded preparation skip: 5 cases")
    assert files["skipped"].is_file() and "benchmark" not in files


def test_the_warm_up_leaves_out_a_coded_skip_and_warms_the_next_cases(tmp_path, monkeypatch):
    first = list(REFUSED)[:3]
    phone, _files, problems, _results = measured(tmp_path, monkeypatch, {"warmup": {"iterations": 5, "jobs": [], "cases": 3}},
                                                 cases=(*first, "a", "b"), refuse=REFUSED)
    warmed = [args[args.index("case") + 1] for args in phone.arguments if "warmup" in args]
    assert warmed == [",".join(first), "a,b"]
    launched = [case for case in variant_order.shuffled(RUN["orderSeed"])(1, [*first, "a", "b"]) if case in first]
    assert [line for line in problems if not line.startswith("not_measured: ")] == [f"case_skipped: {case}: keystore_unsupported" for case in launched]


RAILS = "no_power_rails: the device reports no power rails"
REFUSED_PLAN = ("INSTRUMENTATION_STATUS: stack=io.github.junekim0007.cryptobench.benchmark.RefusedPlanException: refused_plan: {0}\n"
                "Tests run: 1,  Failures: 1\nINSTRUMENTATION_CODE: -1\n")


class RefusingPhone(Phone):
    """The plan check refuses every case: the listing dies on RefusedPlanException after RunnablePlan wrote each refusal to skipped.yaml."""

    def __init__(self, folder, run_wide=None, **options):
        super().__init__(folder, **options)
        self.run_wide = run_wide

    def instrument(self, test_class, *arguments, step="instrument"):
        if "log" not in arguments:
            return super().instrument(test_class, *arguments, step=step)
        self.log.append(f"list {test_class}")
        if self.run_wide:
            return REFUSED_PLAN.format(self.run_wide)
        self.skips = [{"stage": "benchmark", "provider": "P", "type": "T", "name": c, "caseId": c, "code": "no_power_rails", "reason": RAILS}
                      for c in self.cases]
        self.cases = []
        return REFUSED_PLAN.format("; ".join(f"{c}: {RAILS}" for c in ("a", "b")))


@pytest.mark.parametrize("warmup", [0, 5])
def test_a_plan_whose_every_case_the_check_refused_is_all_cases_skipped(tmp_path, monkeypatch, capsys, warmup):
    phone = RefusingPhone(tmp_path)
    run = {"warmup": {"iterations": warmup, "jobs": [], "cases": 3}}
    _phone, files, problems, _results = measured(tmp_path, monkeypatch, run, phone=phone)
    out = capsys.readouterr().out.splitlines()
    assert [line for line in out if line.startswith("case_skipped: ")] == ["case_skipped: a: no_power_rails", "case_skipped: b: no_power_rails"]
    assert problems == ["all_cases_skipped: every case of CryptoBenchmark is refused by the plan check: 2 skips, listed in skipped.yaml"]
    assert [r["code"] for r in yaml.safe_load(files["skipped"].read_text())["skipped"]] == ["no_power_rails"] * 2
    assert yaml.safe_load(files["prepared"].read_text())["cases"] is None and "benchmark" not in files
    assert not [s for s in steps(phone) if s.startswith("instrument ")]


@pytest.mark.parametrize("warmup", [0, 5])
def test_a_run_wide_refusal_stops_with_the_devices_words(tmp_path, monkeypatch, warmup):
    phone = RefusingPhone(tmp_path, run_wide="not_positive: processRepetitions 0")
    with pytest.raises(DeviceError, match=r"(?s)CryptoBenchmark planned no case on the device:.*refused_plan: not_positive: processRepetitions 0"):
        measured(tmp_path, monkeypatch, {"warmup": {"iterations": warmup, "jobs": [], "cases": 3}}, phone=phone)


def test_every_case_failing_stops_the_run(tmp_path, monkeypatch):
    with pytest.raises(DeviceError, match="failed on the device for every case"):
        measured(tmp_path, monkeypatch, {}, cases=("a",), crash=("a",))


def test_each_pass_is_its_own_session_and_every_metric_comes_from_its_pass(tmp_path, monkeypatch):
    run = {"metrics": ["TIME", "ALLOCATION"], "harness": {"energy": {"capture": "measured"}},
           "passes": {"timing": {"samples": 300}, "energy": {"samples": 3, "minWindowSeconds": 5}, "allocation": {"samples": 100}}}
    phone, files, _problems, results = measured(tmp_path, monkeypatch, run)
    named = [args[args.index("cryptobench.pass") + 1] + ":" + args[args.index("cryptobench.samples") + 1] for args in phone.arguments]
    # the fake phone's 3 samples are a 0.3 s window, short of 5 s: each energy case is launched once more with 3 x 1.5 x 5 / 0.3 samples
    assert named == ["timing:300", "timing:300", "energy:3", "energy:75", "energy:3", "energy:75", "allocation:100", "allocation:100"]
    assert steps(phone).count("window open") == 1 and steps(phone).index("window open") > steps(phone).index("instrument CryptoBenchmark b")
    # the energy pass converts again after the end idle reading, which follows the last pass
    assert [c.split("--metrics=")[1].split(" --thermal")[0] for c in phone.converted] == ["TIME", "TIME --uncleaned", "TIME,ALLOCATION",
                                                                                         "TIME --uncleaned"]
    merged = json.loads((results / "benchmark/benchmark.json").read_text())["cases"][0]["metrics"]
    assert merged == {"timeNs": {"runs": [1.0]}, "energyJ": {"runs": [2.0]}, "allocationCount": {"runs": [3.0]}}
    assert len(files["clocks"]) == 3 and files["clocks"][0] == results / "benchmark/timing/clocks.yaml"


class UnevenPhone(Phone):
    """Each process's samples last their own ns, as the emulator's did: process 1 short of the window at 3 samples, process 2 not."""

    def __init__(self, folder, ns, **options):
        super().__init__(folder, **options)
        self.ns = ns

    def pulled(self, remote, local, check):
        if remote == self.data and self.written:
            ns = self.ns[self.log.count("clear") - 1]
            cases = [{**jetpack_case(c), "metrics": {"timeNs": {"runs": [ns] * self.samples}}} for c in self.written]
            pathlib.Path(local).write_text(json.dumps({"context": {"build": {"model": "fake"}}, "benchmarks": cases}))
            return OK
        return super().pulled(remote, local, check)


def test_every_energy_process_holds_the_count_the_first_sized_so_the_runs_merge_as_equals(tmp_path, monkeypatch):
    run = {"harness": {"energy": {"capture": "measured"}}, "passes": {"energy": {"samples": 3, "minWindowSeconds": 5}}, "processRepetitions": 2}
    phone = UnevenPhone(tmp_path, (1e7, 2e8))
    _phone, _files, problems, results = measured(tmp_path, monkeypatch, run, phone=phone)
    asked = [int(a[a.index("cryptobench.samples") + 1]) for a in phone.arguments]
    assert asked == [3, 75, 3, 75, 75, 75]
    folder = results / "benchmark/energy"
    held = [{p.stem: len(json.loads(p.read_text())["benchmarks"][0]["metrics"]["timeNs"]["runs"]) for p in (folder / f"process-{n}/cases").glob("*.json")}
            for n in (1, 2)]
    assert held == [{"a": 75, "b": 75}] * 2
    assert [line for line in problems if line.startswith("short_window")] == [] and steps(phone).count("merge") >= 1


def test_the_throttle_sleep_reaches_every_process_and_unset_passes_nothing(tmp_path, monkeypatch):
    phone, _files, _problems, _results = measured(tmp_path, monkeypatch, {"thermalThrottleSleepSeconds": 30})
    assert all(args[args.index("androidx.benchmark.thermalThrottle.sleepDurationSeconds") + 1] == "30" for args in phone.arguments)
    phone, _files, _problems, _results = measured(tmp_path / "unset", monkeypatch, {})
    assert not any("androidx.benchmark.thermalThrottle.sleepDurationSeconds" in args for args in phone.arguments)


def test_measured_energy_without_its_own_pass_is_refused(tmp_path, monkeypatch):
    with pytest.raises(SystemExit) as stopped, reported():
        measured(tmp_path, monkeypatch, {"harness": {"energy": {"capture": "measured"}}})
    assert stopped.value.code == 1


def test_dry_capture_is_refused_with_passes(tmp_path, monkeypatch):
    with pytest.raises(SystemExit) as stopped, reported():
        measured(tmp_path, monkeypatch, {"harness": {"energy": {"capture": "dry"}}, "passes": {"timing": {"samples": 3}}})
    assert stopped.value.code == 1


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
    phone, _files, problems, results = measured(tmp_path, monkeypatch, {}, thermal=DUMP)
    assert phone.log.count("thermal") == 2 + 2 * 2
    reading = json.loads((results / "benchmark/thermal.json").read_text())
    assert reading["cases"]["a"] == {"start": {"cpu7": 41.5}, "end": {"cpu7": 41.5}, "startStatus": 1, "endStatus": 1}
    assert any("--thermal=" in converted for converted in phone.converted) and problems == []


def test_temperature_unavailable_is_null_with_a_reason_and_no_case_fails(tmp_path, monkeypatch):
    phone, _files, problems, results = measured(tmp_path, monkeypatch, {})
    reading = json.loads((results / "benchmark/thermal.json").read_text())["cases"]["b"]
    assert reading["start"] is None and reading["endStatus"] is None and reading["note"].startswith("thermal_unavailable: ")
    assert problems == [] and json.loads((results / "benchmark/benchmark.json").read_text())["cases"]


def test_the_warm_up_runs_once_before_the_first_pass_and_never_reaches_the_results(tmp_path, monkeypatch):
    run = {"warmup": {"iterations": 10, "jobs": [{"provider": "P", "type": "T", "name": "b"}], "cases": 3},
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
    phone, _files, problems, results = measured(tmp_path, monkeypatch, {"warmup": {"iterations": 5, "jobs": [], "cases": 3}},
                                                cases=("a", "b"), crash=("a,b",))
    assert problems == []
    assert len(json.loads((results / "benchmark/benchmark.json").read_text())["cases"]) == 2


def test_the_cool_down_sleeps_between_cases_never_before_the_first(tmp_path, monkeypatch):
    slept = []
    monkeypatch.setattr(cooldown_hook.time, "sleep", slept.append)
    measured(tmp_path, monkeypatch, {"caseCooldownSeconds": 20})
    assert slept == [20]
    measured(tmp_path / "off", monkeypatch, {})
    assert slept == [20]


def test_an_order_seed_launches_each_process_in_its_drawn_order_and_changes_nothing_else(tmp_path, monkeypatch):
    def run(folder, seed):
        folder.mkdir()
        phone, _files, problems, _results = measured(folder, monkeypatch, {"processRepetitions": 2, **({"orderSeed": seed} if seed else {})},
                                                     cases=tuple("abcdef"))
        launched = [line.split()[-1] for line in steps(phone) if line.startswith("instrument CryptoBenchmark ")]
        return launched, [line for line in steps(phone) if not line.startswith("instrument ")], problems
    plain, seeded = run(tmp_path / "plain", None), run(tmp_path / "seeded", 11)
    assert seeded[0] == variant_order.shuffled(11)(1, list("abcdef")) + variant_order.shuffled(11)(2, list("abcdef"))
    assert sorted(plain[0]) == sorted(seeded[0]) and plain[0] != seeded[0] and plain[1:] == seeded[1:]


def test_variants_run_interleaved_per_item_each_in_its_own_process(tmp_path, monkeypatch):
    cases = ("m_fixed", "m_notFixed", "c_fixed", "c_notFixed")
    phone, _files, _problems, _results = measured(tmp_path, monkeypatch, {"processRepetitions": 2}, cases=cases)
    run = [line.split()[-1] for line in steps(phone) if line.startswith("instrument CryptoBenchmark ")]
    assert run == ["m_fixed", "m_notFixed", "c_fixed", "c_notFixed", "m_notFixed", "m_fixed", "c_notFixed", "c_fixed"]


def test_an_all_refused_run_exits_0_and_its_manifest_counts_the_skips(tmp_path, monkeypatch):
    from test_rerun_safety import Rerun, manifest_of
    rerun = Rerun(tmp_path, monkeypatch, RefusingPhone(tmp_path))
    assert rerun() in (None, 0)
    written = manifest_of(rerun.device)
    assert written["problems"] == ["all_cases_skipped: every case of CryptoBenchmark is refused by the plan check: 2 skips, listed in skipped.yaml"]
    assert written["counts"] == {"prepared": 0, "skipped": 2}


class DryPhone(Phone):
    """EnergyDryBenchmark on the fake phone: one capture[<id>] test per case; a case preparation refused is an assumption failure (assumed),
    or, as the device did before, a failed test."""

    def __init__(self, folder, assumed=True, dry_cases=None, **options):
        super().__init__(folder, **options)
        self.assumed, self.dry, self.dry_cases = assumed, [], list(dry_cases or self.cases)

    def shell(self, command):
        if "perfetto --txt" in command:
            return "4242"
        return "" if command.startswith("kill ") else super().shell(command)

    def instrument(self, test_class, *arguments, step="instrument"):
        if test_class != "EnergyDryBenchmark":
            return super().instrument(test_class, *arguments, step=step)
        self.log.append("instrument EnergyDryBenchmark")
        refused = [c for c in self.dry_cases if c in self.refuse]
        self.skips += [self.refuse[c] for c in refused]
        self.dry = [c for c in self.dry_cases if c not in self.refuse]
        lines = "".join(f"INSTRUMENTATION_STATUS: test=capture[{c}]\nINSTRUMENTATION_STATUS_CODE: 1\n" +
                        (f"INSTRUMENTATION_STATUS: stack=org.junit.AssumptionViolatedException: not_prepared: {c}\nINSTRUMENTATION_STATUS_CODE: -4\n"
                         if c in refused and self.assumed else NOT_PREPARED.format(c, 0, 0).split("Tests run")[0] if c in refused else
                         "INSTRUMENTATION_STATUS_CODE: 0\n") for c in self.dry_cases)
        n = len(self.dry_cases)
        return lines + (f"OK ({n} tests)\n" if self.assumed or not refused else f"Tests run: {n},  Failures: {len(refused)}\n")

    def pull(self, remote, local):
        if remote.endswith("energy-dry.yaml"):
            # EnergyDryBenchmark writes the file empty before its first case
            pathlib.Path(local).write_text("".join(f'"{c}": 1000\n' for c in self.dry))
            return
        super().pull(remote, local)


DRY = {"harness": {"energy": {"capture": "dry"}}}


def test_a_dry_case_preparation_skipped_is_a_skip_and_the_others_are_measured(tmp_path, monkeypatch):
    refused = next(iter(REFUSED))
    phone = DryPhone(tmp_path, cases=("a", refused, "b"), refuse=REFUSED)
    _phone, files, problems, results = measured(tmp_path, monkeypatch, DRY, phone=phone)
    assert problems == [f"case_skipped: {refused}: keystore_unsupported"]
    assert yaml.safe_load((results / "benchmark/energy-dry.yaml").read_text()) == {"a": 1000, "b": 1000}
    assert "instrument EnergyDryBenchmark" in steps(phone) and "joules" in steps(phone)


def test_a_dry_pass_whose_every_case_preparation_skipped_is_all_cases_skipped(tmp_path, monkeypatch):
    phone = DryPhone(tmp_path, cases=tuple(REFUSED), refuse=REFUSED)
    _phone, files, problems, _results = measured(tmp_path, monkeypatch, DRY, phone=phone)
    assert problems[:-1] == [f"case_skipped: {case}: keystore_unsupported" for case in REFUSED]
    assert problems[-1] == "all_cases_skipped: every case of EnergyDryBenchmark is a coded preparation skip: 5 cases, listed in skipped.yaml"
    assert files["skipped"].is_file() and "benchmark" not in files


def test_a_dry_skip_the_device_still_reports_as_a_failed_test_stops_the_dry_only_run(tmp_path, monkeypatch):
    refused = next(iter(REFUSED))
    with pytest.raises(DeviceError, match="EnergyDryBenchmark failed on the device"):
        measured(tmp_path, monkeypatch, DRY, phone=DryPhone(tmp_path, assumed=False, cases=("a", refused), refuse=REFUSED))


def test_every_dry_case_skipped_beside_a_timed_case_keeps_the_processes_measured_joules(tmp_path, monkeypatch):
    dry = list(REFUSED)

    def joules(self, captures, capability, preparation, data, traces, energy_dry, out):
        # energy.py reads energy-dry.yaml for a dry capture: without it the process's joules are lost
        if not energy_dry.is_file():
            raise EnergyError(f"apps/benchmark-runner/energy/energy.py: missing_file: {energy_dry}")
        self.phone.log.append("joules")
        out.write_text(json.dumps({"cases": {"a": {"joules": 1.0}}}))
    monkeypatch.setattr(Energy, "joules", joules)
    phone = DryPhone(tmp_path, cases=("a",), dry_cases=dry, refuse=REFUSED)
    providers = {"P": {"T": {"a": {}, **{case: {"harness": {"energy": {"capture": "dry"}}} for case in dry}}}}
    _phone, files, problems, results = measured(tmp_path, monkeypatch, {}, phone=phone, providers=providers)
    assert problems == [f"case_skipped: {case}: keystore_unsupported" for case in dry]
    assert json.loads((results / "benchmark/energy.json").read_text()) == {"cases": {"a": {"joules": 1.0}}}
    assert (results / "benchmark/energy-dry.yaml").read_text() == "" and "benchmark" in files
    assert [s for s in steps(phone) if s.startswith("instrument ")] == ["instrument CryptoBenchmark a", "instrument EnergyDryBenchmark"]
