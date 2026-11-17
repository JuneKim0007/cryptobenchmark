"""Stops and reruns into one results root, through pipeline.main on the fake phone: the probe and configure are faked, publish, measure and manifest are real."""
import argparse, itertools, json, os, pathlib, subprocess, sys

import pytest
import yaml

import pipeline
from cryptobench.shared.device.adb import DeviceError
from cryptobench.shared.errors.input_error import InputError
from cryptobench.shared import paths
from cryptobench.stages.discovery import discover
from cryptobench.stages.verification import check
from fake_phone import Phone
import test_device_benchmark_flow as flow
from test_manifest import PROBE

FLAGS = {"probe": False, "identify": False, "devices": False, "interop": None, "harness": None, "check": False, "bench": False, "device": True, "config": None,
         "discovery": "overwrite"}
STAMPS = (f"20261117T1200{n:02d}Z" for n in itertools.count())
# facts.yaml a device discovery writes beside the capture; None writes none
FACTS = None


class Rerun:
    """One results root, one fake phone, one global.yaml; each call is a whole pipeline run with these run settings."""

    def __init__(self, tmp_path, monkeypatch, phone=None):
        self.root, self.monkeypatch = tmp_path / "results", monkeypatch
        self.phone = phone or Phone(tmp_path)
        self.phone.connect = lambda: None
        configuration = tmp_path / "global.yaml"
        configuration.write_text("run: {}\n")
        monkeypatch.setattr(pipeline, "global_config", lambda _config: configuration)
        monkeypatch.setattr(pipeline.config_check, "parsed", lambda _file: {"bundled": []})
        monkeypatch.setattr(pipeline.dependencies, "check", lambda *_arguments: None)
        monkeypatch.setattr(pipeline, "Device", lambda *_arguments: self.phone)
        monkeypatch.setattr(pipeline.guide, "write", lambda effective, _capture: written(paths.Configuration.holding(effective).guide, "{}"))
        flow.measured_fakes(monkeypatch, self.phone)

    def __call__(self, run=None, **flags):
        settings = {**flow.RUN, **(run or {})}
        self.monkeypatch.setattr(discover, "discover_in_place", lambda _o, _c, _d, stage, _s: probed(stage, settings))
        options = {**vars(flow.OPTIONS), **FLAGS, "results": str(self.root), **flags}
        self.monkeypatch.setattr(pipeline, "parse_options", lambda: argparse.Namespace(**options))
        return pipeline.main()

    @property
    def device(self):
        [folder] = [p for p in self.root.iterdir() if p.is_dir() and not p.name.startswith(".")]
        return folder

    def aside(self):
        return sorted(paths.RunTree(self.device).superseded.iterdir())


def written(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def probed(stage, run):
    """What discover_in_place leaves in a stage: one capture and its trial, effective.yaml with this run section."""
    stamp = next(STAMPS)
    tree = paths.RunTree(stage)
    capture = written(tree.discovery.root / f"probe_{stamp}.yaml", yaml.safe_dump(PROBE))
    written(tree.discovery.trial(stamp), "{}")
    if FACTS is not None:
        written(tree.discovery.facts, yaml.safe_dump(FACTS))
    written(tree.configuration.effective, yaml.safe_dump({"runId": stamp, "run": run, "providers": {}}, sort_keys=False))
    return discover.located(stage, capture.name)


def manifest_of(folder):
    return yaml.safe_load(paths.RunTree(folder).manifest.read_text())


def test_a_probe_over_a_finished_run_moves_the_measured_unit_aside_whole(tmp_path, monkeypatch):
    rerun = Rerun(tmp_path, monkeypatch)
    rerun()
    measured = manifest_of(rerun.device)
    rerun(probe=True)
    [aside] = rerun.aside()
    assert manifest_of(aside) == measured and (aside / measured["files"]["benchmark"]).is_file()
    assert (aside / measured["files"]["effective"]).is_file() and "benchmark" not in manifest_of(rerun.device)["files"]
    assert not paths.RunTree(rerun.device).benchmark.root.exists()


def test_a_check_on_a_finished_run_publishes_beside_it(tmp_path, monkeypatch):
    rerun = Rerun(tmp_path, monkeypatch)
    rerun()
    tree = paths.RunTree(rerun.device)
    measured, effective = manifest_of(rerun.device), tree.configuration.effective.read_text()
    monkeypatch.setattr(check, "on_device", lambda *arguments: written(paths.CheckFolder(arguments[-1]).result, CHECKED))
    monkeypatch.setattr(check.answers, "write_known_answers", lambda effective, *_rest: written(paths.Configuration.holding(effective).known_answers, "{}"))
    rerun(check=True)
    after = manifest_of(rerun.device)
    assert after["files"] == {**measured["files"], "check": "check/check.yaml"} and tree.configuration.effective.read_text() == effective
    assert tree.benchmark.json.is_file() and tree.check.result.is_file() and not tree.superseded.exists()
    assert len(tree.discovery.captures()) == 2
    ran_with = tree.check.configuration
    assert all(f.is_file() for f in (ran_with.effective, ran_with.guide, ran_with.known_answers)) and not tree.configuration.known_answers.exists()


CHECKED = yaml.safe_dump({"summary": {"cases": 1, "outcomes": {"pass": 1}, "oracles": {}}, "cases": [{"id": "a", "outcome": "pass"}]})


def test_a_check_into_a_new_folder_is_its_own_unit(tmp_path, monkeypatch):
    rerun = Rerun(tmp_path, monkeypatch)
    monkeypatch.setattr(check, "on_device", lambda *arguments: written(paths.CheckFolder(arguments[-1]).result, CHECKED))
    monkeypatch.setattr(check.answers, "write_known_answers", lambda effective, *_rest: written(paths.Configuration.holding(effective).known_answers, "{}"))
    rerun(check=True)
    files = manifest_of(rerun.device)["files"]
    assert {files["check"], files["guide"], files["knownAnswers"]} == {"check/check.yaml", "configuration/guide.yaml", "configuration/known-answers.yaml"}
    assert all((rerun.device / path).is_file() for path in files.values())


def test_a_rerun_reports_what_superseded_holds_at_its_end(tmp_path, monkeypatch, capsys):
    rerun = Rerun(tmp_path, monkeypatch)
    rerun()
    assert "superseded_kept" not in capsys.readouterr().out
    rerun()
    last = capsys.readouterr().out.splitlines()[-1]
    assert last.startswith(f"warning: superseded_kept: {paths.RunTree(rerun.device).superseded}: 1 earlier unit, ")


def test_a_partial_manifest_is_not_a_finished_device(tmp_path):
    written(tmp_path / "done/manifest.yaml", "schemaVersion: 1\n")
    written(tmp_path / "stopped/manifest.yaml", yaml.safe_dump({"schemaVersion": 1, "partial": {"reason": "interrupted"}}))
    assert paths.Results(tmp_path).devices() == ["done"]
    assert paths.finished(tmp_path / "done") and not paths.finished(tmp_path / "stopped") and not paths.finished(tmp_path / "none")


def stopped_at(phone, monkeypatch, case, error):
    measured = phone.instrument

    def stops(test_class, *arguments, step="instrument"):
        if case in arguments:
            raise error
        return measured(test_class, *arguments, step=step)
    monkeypatch.setattr(phone, "instrument", stops)


def test_a_stopped_run_writes_a_partial_manifest_and_a_rerun_keeps_it_whole_aside(tmp_path, monkeypatch):
    rerun = Rerun(tmp_path, monkeypatch, Phone(tmp_path, cases=("a", "b", "c")))
    stopped_at(rerun.phone, monkeypatch, "b", KeyboardInterrupt())
    with pytest.raises(KeyboardInterrupt):
        rerun()
    stopped = manifest_of(rerun.device)
    assert stopped["partial"] == {"reason": "interrupted", "caseRuns": 1, "cases": 1, "processes": {".": 1}}
    assert stopped["files"]["prepared"] == "preparation/prepared.yaml" and rerun.phone.log[-3:] == ["pull prepared.yaml", "pull skipped.yaml", "pull pins"]
    assert not paths.finished(rerun.device) and paths.Results(rerun.root).devices() == []
    monkeypatch.undo()
    rerun = Rerun(tmp_path, monkeypatch, Phone(tmp_path, cases=("a", "b", "c")))
    rerun()
    [aside] = rerun.aside()
    assert manifest_of(aside) == stopped and json.loads((aside / "benchmark/cases/a.json").read_text())["benchmarks"]
    assert (aside / stopped["files"]["effective"]).is_file() and not (aside / "benchmark/cases/b.json").exists()
    assert paths.finished(rerun.device) and sorted(p.stem for p in paths.RunTree(rerun.device).benchmark.cases.iterdir()) == ["a", "b", "c"]


def test_a_run_that_fails_part_way_names_its_error_in_the_partial_manifest(tmp_path, monkeypatch):
    rerun = Rerun(tmp_path, monkeypatch, Phone(tmp_path, cases=("a", "b")))
    stopped_at(rerun.phone, monkeypatch, "b", DeviceError("adb shell: closed by the test"))
    with pytest.raises(DeviceError):
        rerun()
    assert manifest_of(rerun.device)["partial"]["reason"] == "DeviceError: adb shell: closed by the test"


HOLD = "import sys; from cryptobench.shared.results.lock import DeviceLock; DeviceLock.take(sys.argv[1]); print('held', flush=True); sys.stdin.read()"


def test_a_second_run_on_the_same_results_root_is_device_busy_and_writes_nothing(tmp_path, monkeypatch):
    rerun = Rerun(tmp_path, monkeypatch)
    rerun.root.mkdir()
    library = pathlib.Path(paths.__file__).parents[3]
    holder = subprocess.Popen([sys.executable, "-c", HOLD, str(rerun.root)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
                              env={**os.environ, "PYTHONPATH": str(library)})
    try:
        assert holder.stdout.readline().strip() == "held"
        with pytest.raises(InputError, match=rf"^device_busy: {rerun.root} is in use by another run \(pid {holder.pid}\)"):
            rerun()
        assert sorted(p.name for p in rerun.root.iterdir()) == [paths.LOCK]
    finally:
        holder.stdin.close()
        holder.wait(10)
    rerun()
    assert paths.finished(rerun.device)


def test_fewer_repetitions_on_a_rerun_leave_no_process_folder_of_the_earlier_run(tmp_path, monkeypatch):
    rerun = Rerun(tmp_path, monkeypatch)
    rerun({"processRepetitions": 3})
    rerun({"processRepetitions": 2})
    benchmark = paths.RunTree(rerun.device).benchmark.root
    assert sorted(p.name for p in benchmark.glob("process-*")) == ["process-1", "process-2"]
    [aside] = rerun.aside()
    assert sorted(p.name for p in (aside / "benchmark").glob("process-*")) == ["process-1", "process-2", "process-3"]
    assert manifest_of(rerun.device)["files"]["clocks"] == [f"benchmark/process-{n}/clocks.yaml" for n in (1, 2)]


def test_fewer_passes_on_a_rerun_leave_no_pass_folder_of_the_earlier_run(tmp_path, monkeypatch):
    rerun = Rerun(tmp_path, monkeypatch)
    rerun({"metrics": ["TIME", "ALLOCATION"], "passes": {"timing": {"samples": 3}, "allocation": {"samples": 3}}})
    rerun({"metrics": ["TIME"]})
    assert sorted(p.name for p in paths.RunTree(rerun.device).benchmark.root.iterdir() if p.is_dir()) == ["blocks", "cases"]
    [aside] = rerun.aside()
    assert sorted(p.name for p in (aside / "benchmark").iterdir() if p.is_dir()) == ["allocation", "timing"]
    assert json.loads((aside / "benchmark/benchmark.json").read_text())["cases"]
