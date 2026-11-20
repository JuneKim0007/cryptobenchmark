"""Resuming a stopped run by blocks of run.resumeBlockRuns, through pipeline.main on the fake phone: the probe and configure are faked; publish,
measure, the block records and the manifest are real."""
import json

import pytest
import yaml

import test_rerun_safety
from cryptobench.shared import paths
from cryptobench.shared.results import identity, run_record
from cryptobench.stages.measurement.session import variant_order
from fake_phone import PROBE, Energy, Phone
from test_device_benchmark_flow import MEASURED
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
real_code = identity.code
FACTS = {"schemaVersion": 1, "build": {"securityPatch": "2026-10-05", "apex": {"com.android.conscrypt": 1, "com.android.art": 1}}}


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
        "schemaVersion": 3, "pass": None, "block": 3, "runs": {"first": 5, "last": 6}, "repetitions": 7, "size": 2,
        "bootId": {"start": "boot-1", "end": "boot-1"}, "outcome": "finished"}
    assert [run["folder"] for run in third["processes"]] == ["process-5", "process-6"] and third["processes"][0]["problems"] == []
    assert third["processes"][0]["relaunched"] == []
    assert sorted(third["processes"][0]["files"]) == ["benchmark.json", "benchmarkData.json", "cases/a.json", "cases/b.json", "clocks.yaml", "order.txt",
                                                         "thermal.json"]
    assert sorted(third["identity"]) == ["clean", "code", "commit", "device", "energyAcceptUnresponsive", "order", "run", "schema", "selection",
                                        "suppressErrors"]
    assert sorted(third["identity"]["code"]) == ["runner", "timed"] and len(third["identity"]["commit"]) == 40
    assert third["identity"]["run"]["resumeBlockRuns"] == 2 and third["identity"]["order"] == variant_order.chosen(4792)[1]
    assert third["identity"]["suppressErrors"] == [] and third["runId"].endswith("Z")
    assert record(rerun.device, 4)["runs"] == {"first": 7, "last": 7}


@pytest.mark.parametrize("change, named", [
    (lambda monkeypatch: {"launchRetries": 1}, "run.launchRetries"),
    (lambda monkeypatch: {"orderSeed": 7}, "order, run.orderSeed"),
    (lambda monkeypatch: monkeypatch.setattr(test_rerun_safety, "FLAGS", {**test_rerun_safety.FLAGS, "suppress_errors": "UNLOCKED"}) or {},
     "suppressErrors"),
    (lambda monkeypatch: monkeypatch.setattr(test_rerun_safety, "FACTS", {**FACTS, "build": {**FACTS["build"], "securityPatch": "2026-11-05"}}) or {},
     "device.build.securityPatch"),
    (lambda monkeypatch: monkeypatch.setattr(test_rerun_safety, "FACTS", {**FACTS, "build": {**FACTS["build"], "apex": {**FACTS["build"]["apex"],
                                                                                                                  "com.android.art": 2}}}) or {},
     "device.build.apex.com.android.art"),
    (lambda monkeypatch: monkeypatch.setattr(test_rerun_safety, "FACTS", {"schemaVersion": 1}) or {}, "device.build"),
    (lambda monkeypatch: monkeypatch.setattr(identity, "code", lambda: {**real_code(), "runner": "edited"}) or {}, "code.runner"),
    (lambda monkeypatch: monkeypatch.setattr(identity, "code", lambda: {**real_code(), "timed": "edited"}) or {}, "code.timed"),
    (lambda monkeypatch: monkeypatch.setattr(test_rerun_safety, "PROBE", {**PROBE, "runtime": {**PROBE["runtime"], "release": "17.1"}}) or {},
     "device.release"),
])
def test_a_changed_identity_starts_fresh_and_names_what_changed(tmp_path, monkeypatch, capsys, change, named):
    monkeypatch.setattr(test_rerun_safety, "FACTS", FACTS)
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


def test_a_kept_runs_changed_case_file_is_rejected_and_only_that_case_launched_again_in_it(tmp_path, monkeypatch, capsys):
    rerun = Rerun(tmp_path, monkeypatch)
    stopped(rerun, SEVEN, launch=2 * 6 + 1)
    paths.RunTree(rerun.device).benchmark.process(3).case("a").write_text("{}")
    stop = Stop(rerun.phone, monkeypatch)
    capsys.readouterr()
    rerun(SEVEN)
    out = capsys.readouterr().out.splitlines()
    assert out.index("resumed:   kept blocks 1-3 (runs 1-6), restarting at run 7") < out.index("redo:      run 3: a (result_mismatch)") < \
        next(n for n, line in enumerate(out) if line.startswith("measure:"))
    assert not [line for line in out if "block_unverified" in line] and stop.launches == 1 + 2
    assert [named for _test, named in rerun.phone.ran[-3:]] == ["a", "a", "b"]
    entry = record(rerun.device, 2)["processes"][0]
    assert entry["repetition"] == 3 and entry["relaunched"] == [{"case": "a", "attempt": 1, "code": "result_mismatch"}] and entry["findings"] == []
    [rejected] = paths.RunTree(rerun.device).rejected.iterdir()
    assert (rejected / "process-3/a.json").read_text() == "{}"
    validation = yaml.safe_load(paths.RunTree(rerun.device).validation.read_text())["runs"]
    assert validation["process-3"]["checkedBy"] == "block_end" and validation["process-1"]["checkedBy"] == "restart"
    assert paths.finished(rerun.device) and json.loads(paths.RunTree(rerun.device).benchmark.process(3).case("a").read_text())["benchmarks"]
    process = paths.RunTree(rerun.device).benchmark.process(3)
    assert sorted(json.loads(process.thermal.read_text())["cases"]) == ["a", "b"] and sorted(yaml.safe_load(process.clocks.read_text())["cases"]) == ["a", "b"]
    assert [b["name"] for b in json.loads(process.data.read_text())["benchmarks"]] == ["measure[a]", "measure[b]"]


def test_a_kept_runs_changed_run_file_is_measured_again_with_every_block_after_it(tmp_path, monkeypatch, capsys):
    rerun = Rerun(tmp_path, monkeypatch)
    stopped(rerun, SEVEN, launch=2 * 6 + 1)
    paths.RunTree(rerun.device).benchmark.process(3).json.write_text("{}")
    capsys.readouterr()
    rerun(SEVEN)
    out = capsys.readouterr().out.splitlines()
    assert [line.split(": ")[2] for line in out if line.startswith("warning: block_unverified")] == [str(paths.RunTree(rerun.device).benchmark.block(2))]
    assert "process-3: files_differ: benchmark.json: its digest differs" in next(line for line in out if "block_unverified" in line)
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


def test_the_same_build_facts_and_suppressed_errors_resume(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(test_rerun_safety, "FACTS", FACTS)
    monkeypatch.setattr(test_rerun_safety, "FLAGS", {**test_rerun_safety.FLAGS, "suppress_errors": "UNLOCKED,EMULATOR"})
    rerun = Rerun(tmp_path, monkeypatch)
    stopped(rerun, SEVEN, launch=2 * 5 + 2)
    monkeypatch.setattr(test_rerun_safety, "FLAGS", {**test_rerun_safety.FLAGS, "suppress_errors": "EMULATOR, UNLOCKED"})
    capsys.readouterr()
    rerun(SEVEN)
    assert lines(capsys, "resumed:") == ["resumed:   kept blocks 1-2 (runs 1-4), restarting at run 5"]
    assert record(rerun.device, 1)["identity"]["device"]["build"] == FACTS["build"]
    assert record(rerun.device, 1)["identity"]["suppressErrors"] == ["EMULATOR", "UNLOCKED"]


def test_os_litter_in_a_kept_run_and_beside_its_records_does_not_unverify_it(tmp_path, monkeypatch, capsys):
    rerun = Rerun(tmp_path, monkeypatch)
    stopped(rerun, SEVEN, launch=2 * 5 + 2)
    benchmark = paths.RunTree(rerun.device).benchmark
    for litter in (benchmark.process(1).root / ".DS_Store", benchmark.process(3).cases / "._a.json", benchmark.blocks / ".DS_Store",
                   benchmark.root / "Thumbs.db"):
        litter.write_bytes(b"\0\1")
    capsys.readouterr()
    rerun(SEVEN)
    out = capsys.readouterr().out.splitlines()
    assert "resumed:   kept blocks 1-2 (runs 1-4), restarting at run 5" in out and not [line for line in out if "block_unverified" in line]
    assert ".DS_Store" not in record(rerun.device, 1)["processes"][0]["files"]


def test_another_commit_of_the_same_code_resumes_and_the_manifest_run_is_every_block_identity(tmp_path, monkeypatch, capsys):
    rerun = Rerun(tmp_path, monkeypatch)
    stopped(rerun, SEVEN, launch=2 * 5 + 2)
    real = run_record.checkout
    monkeypatch.setattr(run_record, "checkout", lambda: {**real(), "commit": "0" * 40, "clean": False})
    capsys.readouterr()
    rerun(SEVEN)
    assert not lines(capsys, "warning: identity_changed")
    run = manifest_of(rerun.device)["run"]
    assert run["commit"] == "0" * 40 and run == record(rerun.device, 3)["identity"]
    assert run_record.changed(record(rerun.device, 1)["identity"], run) == []


def test_the_manifest_names_the_kept_blocks_and_the_run_that_measured_them(tmp_path, monkeypatch):
    rerun = Rerun(tmp_path, monkeypatch)
    stopped(rerun, SEVEN, launch=2 * 5 + 2)
    earlier = record(rerun.device, 1)["runId"]
    assert "resumed" not in manifest_of(rerun.device)
    rerun(SEVEN)
    assert manifest_of(rerun.device)["resumed"] == [{"pass": None, "blocks": "1-2", "runs": "1-4", "runIds": [earlier]}]
    assert earlier and record(rerun.device, 3)["runId"] not in (None, earlier)


def test_a_second_resume_names_each_run_that_measured_a_kept_block(tmp_path, monkeypatch):
    rerun = Rerun(tmp_path, monkeypatch)
    stopped(rerun, SEVEN, launch=2 * 3 + 2)
    stopped(rerun, SEVEN, launch=2 * 2 + 2)
    assert manifest_of(rerun.device)["resumed"][0]["blocks"] == "1" and "partial" in manifest_of(rerun.device)
    rerun(SEVEN)
    first, second = record(rerun.device, 1)["runId"], record(rerun.device, 2)["runId"]
    assert first != second and manifest_of(rerun.device)["resumed"] == [{"pass": None, "blocks": "1-2", "runs": "1-4", "runIds": [first, second]}]


def test_an_old_format_record_starts_fresh_naming_the_schema(tmp_path, monkeypatch, capsys):
    rerun = Rerun(tmp_path, monkeypatch)
    stopped(rerun, SEVEN, launch=2 * 5 + 2)
    for path in paths.RunTree(rerun.device).benchmark.block_records():
        old = yaml.safe_load(path.read_text())
        old["schemaVersion"], old["identity"]["schema"] = 1, 1
        del old["identity"]["suppressErrors"], old["runId"]
        path.write_text(yaml.safe_dump(old))
    capsys.readouterr()
    rerun(SEVEN)
    assert lines(capsys, "warning: identity_changed") == ["warning: identity_changed: schema, suppressErrors; starting fresh"]


def test_a_block_record_lists_each_launch_again_with_the_code_that_caused_it(tmp_path, monkeypatch):
    rerun = Rerun(tmp_path, monkeypatch, Phone(tmp_path, crash={"b"}))
    rerun({"launchRetries": 1})
    assert record(rerun.device, 1)["processes"][0]["relaunched"] == [{"case": "b", "attempt": 1, "code": "case_failed"}]


def test_block_end_records_each_runs_findings_and_validation_yaml_holds_the_last_check_of_every_run(tmp_path, monkeypatch):
    rerun = Rerun(tmp_path, monkeypatch)
    rerun({"processRepetitions": 3, "resumeBlockRuns": 2})
    assert [run["findings"] for run in record(rerun.device, 1)["processes"]] == [[], []]
    validation = yaml.safe_load(paths.RunTree(rerun.device).validation.read_text())
    assert validation == {"schemaVersion": 1, "runs": {f"process-{n}": {"checkedBy": "block_end", "fails": 0, "findings": []} for n in (1, 2, 3)}}


ENERGY_THREE = MEASURED | {"processRepetitions": 3, "resumeBlockRuns": 1}


def invocations(monkeypatch):
    """energy.json per invocation: the start reading's, or the redo's after the end reading; each case names the invocation that read it."""
    count = [0]
    preflight = Energy.preflight

    def counted(self, *arguments):
        count[0] += 1
        return preflight(self, *arguments)

    def joules(self, *paths_given):
        self.phone.log.append("joules")
        out, redo = paths_given[-1], "energy-redo" in str(paths_given[-1])
        out.write_text(json.dumps({"idleBaseline": "interpolated" if redo else "idle_start_only", "cases": {c: {"by": count[0]} for c in ("a", "b")}}))
    monkeypatch.setattr(Energy, "preflight", counted)
    monkeypatch.setattr(Energy, "joules", joules)


def energy_of(rerun, process):
    return json.loads((paths.RunTree(rerun.device).benchmark.root / f"energy/process-{process}/energy.json").read_text())


def test_a_resume_reads_energy_again_only_for_the_processes_it_measured_and_kept_ones_keep_their_energy_and_idle(tmp_path, monkeypatch):
    invocations(monkeypatch)
    rerun = Rerun(tmp_path, monkeypatch)
    stopped(rerun, ENERGY_THREE, launch=4 * 2 + 1)
    kept = [energy_of(rerun, n) for n in (1, 2)]
    rerun(ENERGY_THREE)
    assert [energy_of(rerun, n) for n in (1, 2)] == kept and kept[0]["idleBaseline"] == "idle_start_only"
    assert energy_of(rerun, 3) == {"idleBaseline": "interpolated", "cases": {"a": {"by": 2}, "b": {"by": 2}}}
    assert "idle_start_only" not in " ".join(manifest_of(rerun.device).get("problems") or [])


def test_a_kept_energy_run_failing_one_case_is_measured_again_whole_so_no_earlier_trace_meets_this_invocations_line(tmp_path, monkeypatch, capsys):
    invocations(monkeypatch)
    rerun = Rerun(tmp_path, monkeypatch)
    stopped(rerun, ENERGY_THREE, launch=4 * 3 + 1)
    kept = energy_of(rerun, 1)
    paths.RunTree(rerun.device).benchmark.root.joinpath("energy/process-2/cases/a.json").write_text("{}")
    capsys.readouterr()
    rerun(ENERGY_THREE)
    assert "resumed:   energy pass: kept block 1 (run 1), restarting at run 2" in lines(capsys, "resumed:")
    assert energy_of(rerun, 1) == kept and kept["idleBaseline"] == "idle_start_only"
    for process in (2, 3):
        assert energy_of(rerun, process) == {"idleBaseline": "interpolated", "cases": {"a": {"by": 2}, "b": {"by": 2}}}
