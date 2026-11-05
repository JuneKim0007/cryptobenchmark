"""The guide's pair check across runs on the fake pipeline: pass, fail, could not run, reuse; no model, no device."""
import logging

import yaml
from test_device_flows import APP, Flow, flow  # noqa: F401  the fixture

from perfrepair import run_dir as rd
from perfrepair.app.facts.path_id import path_id
from perfrepair.device.interop import check_pairs
from perfrepair.dto.interop import failed_pairs
from perfrepair.files import read_json
from perfrepair.grouping import interop_plan
from perfrepair.guide.command import main as guide
from perfrepair.log.emit import EVENT_ATTR


def oracle_runs(f: Flow) -> list[int]:
    """Pairs per oracle run."""
    log = f.root / "interop.log"
    return [int(n) for n in log.read_text().splitlines()] if log.is_file() else []


def dossiers(f: Flow) -> dict:
    return read_json(rd.AppPaths(f.device, path_id(APP)).dossiers)


def coded(caplog, code: str) -> int:
    return sum(getattr(r, EVENT_ATTR, {}).get("data", {}).get("code") == code for r in caplog.records)


def test_every_pair_passing_reaches_the_options_as_pass(flow):
    flow.run()
    [pairs] = oracle_runs(flow)
    assert pairs > 0
    groups = read_json(flow.paths.groups)
    assert groups["interop"]["status"] == "checked"
    labels = {o["interop"] for d in dossiers(flow)["dossiers"] for o in d["options"]}
    assert labels == {"pass"} and flow.problems() == {}


def test_a_failed_pair_is_out_of_the_options_before_the_model(flow, monkeypatch):
    monkeypatch.setenv("FAKE_INTEROP", "fail:Fast")
    flow.run()
    assert failed_pairs(read_json(flow.paths.groups))
    doc = dossiers(flow)
    offered = {o["item"] for d in doc["dossiers"] for o in d["options"]}
    assert not any(item.endswith("|Fast") for item in offered)
    assert "interop_failed" in {n["reason"] for n in doc["noOptions"]}
    assert flow.problems() == {}


def test_a_pair_the_oracle_could_not_decide_is_a_coded_line_and_stays_labelled(flow, monkeypatch, caplog):
    monkeypatch.setenv("FAKE_INTEROP", "not_checkable:Fast")
    with caplog.at_level(logging.INFO, "perfrepair"):
        flow.run()
    lines = [getattr(r, EVENT_ATTR)["detail"] for r in caplog.records if getattr(r, EVENT_ATTR, {}).get("data", {}).get("code") == "interop_unverified"]
    assert lines and all(": not_checkable: " in line for line in lines)
    labels = {o["interop"] for d in dossiers(flow)["dossiers"] for o in d["options"]}
    assert "not_checkable" in labels and flow.problems() == {}


def test_a_pair_the_plan_holds_back_counts_among_the_pairs_and_reads_not_checkable(flow, monkeypatch):
    flow.run()
    held = frozenset(next(g for g in read_json(flow.paths.groups)["groups"] if len(g["runnable"]) > 1)["runnable"][:2])
    monkeypatch.setattr(interop_plan, "_across", lambda _, a, b: {a, b} == held)
    done = check_pairs(flow.device, None, True, print)
    assert done.planned == len(done.results) and sum(r.result == "not_checkable" for r in done.results) == 1


def test_an_unchanged_rerun_runs_no_oracle_and_writes_nothing(flow):
    flow.run()
    [pairs] = oracle_runs(flow)
    before = flow.paths.interop.stat().st_mtime_ns, (flow.device / rd.MANIFEST).stat().st_mtime_ns
    flow.run()
    assert oracle_runs(flow) == [pairs] and flow.ended("inbound")[0] == flow.ended("screen")[0] == "reused"
    assert (flow.paths.interop.stat().st_mtime_ns, (flow.device / rd.MANIFEST).stat().st_mtime_ns) == before


def test_another_setup_runs_the_check_again(flow):
    flow.run()
    flow.add_provider()
    flow.run()
    assert len(oracle_runs(flow)) == 2 and flow.problems() == {}


def test_verdicts_of_another_setup_do_not_stay_when_the_check_cannot_run(flow):
    flow.run()
    doc = yaml.safe_load(flow.paths.interop.read_text())
    flow.paths.interop.write_text(yaml.safe_dump({**doc, "setup": {"deviceId": "another"}}, sort_keys=False))
    done = check_pairs(flow.device, None, False, print)
    assert done.pending == done.planned > 0 and oracle_runs(flow) == [done.planned]
    assert read_json(flow.paths.groups)["interop"]["status"] == "not_run"


def test_only_a_pair_with_no_verdict_runs_and_the_others_are_kept(flow):
    flow.run()
    [pairs] = oracle_runs(flow)
    for path in (flow.paths.interop, flow.paths.interop_plan):
        doc = yaml.safe_load(path.read_text())
        doc["pairs"] = doc["pairs"][1:]
        path.write_text(yaml.safe_dump(doc, sort_keys=False))
    flow.run()
    assert oracle_runs(flow) == [pairs, 1]
    assert flow.problems() == {}


def test_a_verdict_at_another_key_size_runs_again(flow):
    flow.run()
    [pairs] = oracle_runs(flow)
    doc = yaml.safe_load(flow.paths.interop.read_text())
    doc["pairs"][0]["keySize"] = 1
    flow.paths.interop.write_text(yaml.safe_dump(doc, sort_keys=False))
    flow.run()
    assert oracle_runs(flow) == [pairs, 1]


def test_a_named_folder_runs_no_oracle_and_says_so_in_one_coded_line(flow, caplog):
    guide(["--app", str(APP), "--agent", "dry-run", "--perfrepair-config", str(flow.settings()), *flow.where(),
           "--stop-after-device", "--device"])
    flow.capsys.readouterr()
    with caplog.at_level(logging.INFO, "perfrepair"):
        guide(["--app", str(APP), "--agent", "dry-run", "--perfrepair-config", str(flow.settings()), "--device-results",
               str(flow.device)])
    assert oracle_runs(flow) == []
    assert coded(caplog, "interop_unverified") == 1
    assert read_json(flow.paths.groups)["interop"]["status"] == "not_run"
