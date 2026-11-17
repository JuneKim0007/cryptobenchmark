"""Resuming a stopped run by blocks of run.resumeBlockRuns, through pipeline.main on the fake phone: the probe and configure are faked; publish,
measure, the block records and the manifest are real."""
import json

import pytest
import yaml

import test_rerun_safety
from cryptobench.shared import paths
from cryptobench.stages.measurement.session import variant_order
from fake_phone import Phone
from test_manifest import PROBE
from test_rerun_safety import Rerun, manifest_of


class Stop:
    """A KeyboardInterrupt at the n-th case launch or the n-th boot id read, once; launches counts every case launch."""

    def __init__(self, phone, monkeypatch, launch=None, boot=None):
        self.launch, self.boot, self.launches, self.boots = launch, boot, 0, 0
        instrument, boot_id = phone.instrument, phone.boot_id

        def instrumented(test_class, *arguments, step="instrument"):
            if "log" not in arguments:
                self.launches += 1
                if self.launches == self.launch:
                    raise KeyboardInterrupt()
            return instrument(test_class, *arguments, step=step)

        def booted():
            self.boots += 1
            if self.boots == self.boot:
                raise KeyboardInterrupt()
            return boot_id()
        monkeypatch.setattr(phone, "instrument", instrumented)
        monkeypatch.setattr(phone, "boot_id", booted)

    def off(self):
        self.launch = self.boot = None
        self.launches = 0


def stopped(rerun, run, **at):
    stop = Stop(rerun.phone, rerun.monkeypatch, **at)
    with pytest.raises(KeyboardInterrupt):
        rerun(run)
    stop.off()
    return stop


def processes(folder):
    return sorted((p.name for p in paths.RunTree(folder).benchmark.root.glob("process-*")), key=lambda name: int(name.split("-")[1]))


def snapshot(folder, names):
    """{process: {file: (inode, bytes)}}: a process kept in place keeps its inodes."""
    benchmark = paths.RunTree(folder).benchmark.root
    return {name: {p.relative_to(benchmark / name).as_posix(): (p.stat().st_ino, p.read_bytes()) for p in (benchmark / name).rglob("*") if p.is_file()}
            for name in names}


def lines(capsys, prefix):
    return [line for line in capsys.readouterr().out.splitlines() if line.startswith(prefix)]


SEVEN = {"processRepetitions": 7, "resumeBlockRuns": 2}


def test_a_stop_in_block_3_keeps_blocks_1_and_2_and_the_result_equals_an_uninterrupted_run(tmp_path, monkeypatch, capsys):
    (tmp_path / "resumed").mkdir()
    (tmp_path / "whole").mkdir()
    rerun = Rerun(tmp_path / "resumed", monkeypatch)
    stop = stopped(rerun, SEVEN, launch=2 * 5 + 2)
    assert processes(rerun.device) == [f"process-{n}" for n in range(1, 7)]
    assert manifest_of(rerun.device)["partial"]["reason"] == "interrupted"
    before = snapshot(rerun.device, [f"process-{n}" for n in range(1, 5)])
    capsys.readouterr()
    rerun(SEVEN)
    out = capsys.readouterr().out.splitlines()
    assert "resumed:   kept blocks 1-2 (runs 1-4), restarting at run 5" in out
    assert stop.launches == 2 * 3 and snapshot(rerun.device, before) == before
    [aside] = rerun.aside()
    assert sorted(p.name for p in (aside / "benchmark").glob("process-*")) == ["process-5", "process-6"]
    assert not (aside / "benchmark/process-1").exists() and (aside / "manifest.yaml").is_file()

    whole = Rerun(tmp_path / "whole", monkeypatch, Phone(tmp_path / "whole"))
    whole(SEVEN)
    assert processes(rerun.device) == processes(whole.device) == [f"process-{n}" for n in range(1, 8)]
    merged = lambda folder: json.loads(paths.RunTree(folder).benchmark.json.read_text())
    assert merged(rerun.device) == merged(whole.device) and [c["id"] for c in merged(rerun.device)["cases"]] == ["a", "b"]
    assert {k: v for k, v in manifest_of(rerun.device)["files"].items() if k != "probe" and k != "trial"} == \
           {k: v for k, v in manifest_of(whole.device)["files"].items() if k != "probe" and k != "trial"}
    assert snapshot(rerun.device, processes(rerun.device)).keys() == snapshot(whole.device, processes(whole.device)).keys()
    records = sorted(p.name for p in paths.RunTree(rerun.device).benchmark.blocks.iterdir())
    assert records == [f"block-{n}.yaml" for n in range(1, 5)]


def test_a_stop_at_a_block_boundary_keeps_every_finished_block(tmp_path, monkeypatch, capsys):
    rerun = Rerun(tmp_path, monkeypatch)
    stopped(rerun, SEVEN, boot=5)
    assert processes(rerun.device) == [f"process-{n}" for n in range(1, 5)]
    capsys.readouterr()
    rerun(SEVEN)
    assert lines(capsys, "resumed:") == ["resumed:   kept blocks 1-2 (runs 1-4), restarting at run 5"]
    [aside] = rerun.aside()
    assert not list((aside / "benchmark").glob("process-*")) and processes(rerun.device) == [f"process-{n}" for n in range(1, 8)]
    assert paths.finished(rerun.device)


def record(folder, block):
    return yaml.safe_load(paths.RunTree(folder).benchmark.block(block).read_text())


def test_a_block_record_names_its_identity_runs_boot_and_files(tmp_path, monkeypatch):
    rerun = Rerun(tmp_path, monkeypatch)
    rerun(SEVEN)
    third = record(rerun.device, 3)
    assert {key: third[key] for key in ("schemaVersion", "pass", "block", "runs", "repetitions", "size", "bootId", "outcome")} == {
        "schemaVersion": 1, "pass": None, "block": 3, "runs": {"first": 5, "last": 6}, "repetitions": 7, "size": 2,
        "bootId": {"start": "boot-1", "end": "boot-1"}, "outcome": "finished"}
    assert [run["folder"] for run in third["processes"]] == ["process-5", "process-6"] and third["processes"][0]["problems"] == []
    assert sorted(third["processes"][0]["files"]) == ["benchmark.json", "benchmarkData.json", "cases/a.json", "cases/b.json", "clocks.yaml", "thermal.json"]
    assert sorted(third["identity"]) == ["code", "device", "order", "run", "schema", "selection"]
    assert third["identity"]["run"]["resumeBlockRuns"] == 2 and third["identity"]["order"] == variant_order.ORDER
    assert record(rerun.device, 4)["runs"] == {"first": 7, "last": 7}


@pytest.mark.parametrize("change, named", [
    (lambda monkeypatch: {"launchRetries": 1}, "run.launchRetries"),
    (lambda monkeypatch: monkeypatch.setattr(variant_order, "ORDER", {"scheme": "interleaved", "seed": 7}) or {}, "order"),
    (lambda monkeypatch: monkeypatch.setattr(test_rerun_safety, "PROBE", {**PROBE, "runtime": {**PROBE["runtime"], "release": "17.1"}}) or {},
     "device.release"),
])
def test_a_changed_identity_starts_fresh_and_names_what_changed(tmp_path, monkeypatch, capsys, change, named):
    rerun = Rerun(tmp_path, monkeypatch)
    stop = stopped(rerun, SEVEN, launch=2 * 5 + 2)
    capsys.readouterr()
    rerun({**SEVEN, **change(monkeypatch)})
    assert lines(capsys, "warning: identity_changed") == [f"warning: identity_changed: {named}; starting fresh"]
    assert stop.launches == 2 * 7
    [aside] = rerun.aside()
    assert [f"process-{n}" for n in range(1, 7)] == sorted((p.name for p in (aside / "benchmark").glob("process-*")), key=lambda n: int(n[8:]))


def test_blocks_larger_than_the_run_are_one_block_and_a_stop_in_it_keeps_nothing(tmp_path, monkeypatch, capsys):
    rerun = Rerun(tmp_path, monkeypatch)
    stop = stopped(rerun, {"processRepetitions": 3}, launch=2 * 2 + 1)
    capsys.readouterr()
    rerun({"processRepetitions": 3})
    assert not lines(capsys, "resumed:") and stop.launches == 2 * 3
    assert record(rerun.device, 1)["runs"] == {"first": 1, "last": 3} and len(rerun.aside()) == 1


def test_blocks_of_one_run_keep_every_run_before_the_stop(tmp_path, monkeypatch, capsys):
    rerun = Rerun(tmp_path, monkeypatch)
    stop = stopped(rerun, {"processRepetitions": 3, "resumeBlockRuns": 1}, launch=2 * 2 + 2)
    capsys.readouterr()
    rerun({"processRepetitions": 3, "resumeBlockRuns": 1})
    assert lines(capsys, "resumed:") == ["resumed:   kept blocks 1-2 (runs 1-2), restarting at run 3"] and stop.launches == 2


def test_one_run_one_block_kept_whole_when_only_the_manifest_was_missing(tmp_path, monkeypatch, capsys):
    rerun = Rerun(tmp_path, monkeypatch)
    rerun()
    paths.RunTree(rerun.device).manifest.unlink()
    stop = Stop(rerun.phone, monkeypatch)
    capsys.readouterr()
    rerun()
    assert lines(capsys, "resumed:") == ["resumed:   kept block 1 (run 1), every run of it measured"] and stop.launches == 0
    assert paths.finished(rerun.device) and paths.RunTree(rerun.device).benchmark.json.is_file()


def test_a_finished_run_is_never_resumed(tmp_path, monkeypatch, capsys):
    rerun = Rerun(tmp_path, monkeypatch)
    rerun(SEVEN)
    stop = Stop(rerun.phone, monkeypatch)
    capsys.readouterr()
    rerun(SEVEN)
    assert not lines(capsys, "resumed:") and stop.launches == 2 * 7


def test_a_record_whose_files_changed_is_measured_again_with_every_block_after_it(tmp_path, monkeypatch, capsys):
    rerun = Rerun(tmp_path, monkeypatch)
    stopped(rerun, SEVEN, launch=2 * 6 + 1)
    paths.RunTree(rerun.device).benchmark.process(3).case("a").write_text("{}")
    capsys.readouterr()
    rerun(SEVEN)
    out = capsys.readouterr().out.splitlines()
    assert [line.split(": ")[2] for line in out if line.startswith("warning: block_unverified")] == [str(paths.RunTree(rerun.device).benchmark.block(2))]
    assert "process-3: its files differ from the record" in next(line for line in out if "block_unverified" in line)
    assert "resumed:   kept block 1 (runs 1-2), restarting at run 3" in out


def test_a_restart_inside_a_block_records_it_unfinished_and_a_rerun_measures_it_again(tmp_path, monkeypatch, capsys):
    rerun = Rerun(tmp_path, monkeypatch)
    boot_id = rerun.phone.boot_id
    reads = iter(["boot-1", "boot-1", "boot-1", "boot-2"])
    monkeypatch.setattr(rerun.phone, "boot_id", lambda: next(reads, None) or boot_id())
    rerun.phone.boot = "boot-2"
    rerun({"processRepetitions": 4, "resumeBlockRuns": 2})
    assert record(rerun.device, 2)["outcome"] == "boot_changed"
    assert "boot_changed: block 2" in manifest_of(rerun.device)["problems"][0]
    paths.RunTree(rerun.device).manifest.unlink()
    capsys.readouterr()
    rerun({"processRepetitions": 4, "resumeBlockRuns": 2})
    out = capsys.readouterr().out.splitlines()
    assert any("block_unverified" in line and "outcome boot_changed" in line for line in out)
    assert "resumed:   kept block 1 (runs 1-2), restarting at run 3" in out


def test_passes_resume_each_pass_from_its_own_first_unfinished_block(tmp_path, monkeypatch, capsys):
    run = {"processRepetitions": 3, "resumeBlockRuns": 1, "metrics": ["TIME", "ALLOCATION"],
           "passes": {"timing": {"samples": 3}, "allocation": {"samples": 3}}}
    rerun = Rerun(tmp_path, monkeypatch)
    stopped(rerun, run, launch=2 * 3 + 2 * 1 + 1)
    capsys.readouterr()
    rerun(run)
    assert lines(capsys, "resumed:") == ["resumed:   timing pass: kept blocks 1-3 (runs 1-3), every run of it measured",
                                         "resumed:   allocation pass: kept block 1 (run 1), restarting at run 2"]
    benchmark = paths.RunTree(rerun.device).benchmark.root
    assert sorted(p.name for p in benchmark.glob("*/process-*")) == ["process-1", "process-1", "process-2", "process-2", "process-3", "process-3"]
    assert sorted(p.name for p in benchmark.glob("process-*")) == ["process-1", "process-2", "process-3"]


def test_a_kept_run_brings_its_problem_lines_so_the_manifest_equals_an_uninterrupted_one(tmp_path, monkeypatch):
    (tmp_path / "resumed").mkdir()
    (tmp_path / "whole").mkdir()
    four = {"processRepetitions": 4, "resumeBlockRuns": 2}
    rerun = Rerun(tmp_path / "resumed", monkeypatch, Phone(tmp_path / "resumed", crash={"b"}))
    stopped(rerun, four, launch=2 * 3 + 1)
    rerun(four)
    whole = Rerun(tmp_path / "whole", monkeypatch, Phone(tmp_path / "whole", crash={"b"}))
    whole(four)
    problems = manifest_of(rerun.device)["problems"]
    assert problems == manifest_of(whole.device)["problems"] and sum("case_failed: b" in line for line in problems) == 4
    assert record(rerun.device, 1)["processes"][0]["problems"] == [problems[0]]


def test_a_new_fingerprint_is_another_device_folder_and_the_stopped_one_stays_as_it_was(tmp_path, monkeypatch, capsys):
    rerun = Rerun(tmp_path, monkeypatch)
    stopped(rerun, SEVEN, launch=2 * 5 + 2)
    [stopped_folder] = [p for p in rerun.root.iterdir() if p.is_dir() and not p.name.startswith(".")]
    before = sorted(p.relative_to(stopped_folder).as_posix() for p in stopped_folder.rglob("*"))
    monkeypatch.setattr(test_rerun_safety, "PROBE", {**PROBE, "runtime": {**PROBE["runtime"], "fingerprint": "fake/other/build"}})
    capsys.readouterr()
    rerun(SEVEN)
    assert not lines(capsys, "resumed:") and not lines(capsys, "warning: identity_changed")
    assert sorted(p.relative_to(stopped_folder).as_posix() for p in stopped_folder.rglob("*")) == before
    assert len([p for p in rerun.root.iterdir() if p.is_dir() and not p.name.startswith(".")]) == 2
