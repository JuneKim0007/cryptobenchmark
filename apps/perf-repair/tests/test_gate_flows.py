"""The benchmark gate through the guide, on the fake pipeline and the dry-run gateway: the used set adding what the test set
lacks, a delta between runs, the stop before any model call. No real device or model is exercised."""
import json

import pytest
import yaml
from cryptobench.paths import RunTree
from perfrepair import run_dir as rd
from perfrepair.files import read_json, read_yaml
from perfrepair.guide.command import main as guide
from test_device_flows import CALLS, GCM_FAST, HMAC, SHA, F, Flow, target

pytestmark = pytest.mark.usefixtures("asked_by_model")
GCM_CALL = 'javax.crypto.Cipher.getInstance("AES/GCM/NoPadding")'


@pytest.fixture
def flow(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(F / "device"))
    monkeypatch.setenv("FAKE_SELECT", "1")
    monkeypatch.setitem(CALLS, GCM_FAST, GCM_CALL)
    f = Flow(tmp_path, capsys)
    f.filter = True
    (tmp_path / "x.yaml").write_text("schemaVersion: 1\ninclude: [{type: Mac}]\n")
    f.sha, f.gcm, f.hmac = target(f, "sha", SHA), target(f, "gcm", GCM_FAST), target(f, "hmac", HMAC)
    return f


def run(flow, *roots, benchmark=None, extra=()):
    path = flow.settings()
    document = yaml.safe_load(path.read_text())
    document["apps"] = {"targets": [str(r) for r in roots], "perfMode": ["latency", "throughput"]}
    document["device"].setdefault("benchmark", {}).update(benchmark or {})
    path.write_text(yaml.safe_dump(document))
    where = () if "--device-results" in extra else flow.where()
    code = guide(["--agent", "dry-run", "--perfrepair-config", str(path), "--on-existing", "resume", *where, *extra])
    captured = flow.capsys.readouterr()
    return code, captured.out.splitlines(), captured.err


def measured(flow):
    return {f"{r['type']}|{r['algorithm']}|{r['provider']}" for r in read_json(RunTree(flow.device).rows)["rows"]}


def coverage(flow):
    return read_yaml(RunTree(flow.device).log.benchmark_coverage)


def deltas(flow):
    return read_yaml(RunTree(flow.device).manifest).get("deltas", [])


def stopped_naming(flow, item):
    """The last run stopped not_benchmarked, the finding naming item."""
    found = [e for e in flow.events() if e["event"] == "finding" and e["data"].get("code") == "not_benchmarked"]
    return [e["outcome"] for e in found] == ["stop"] and item in json.dumps(found)


def test_a_used_item_outside_the_test_set_is_planned_and_measured(flow):
    run(flow, flow.sha)
    assert SHA in measured(flow) and coverage(flow)["items"] == {SHA: "measured"}
    planned = read_yaml(RunTree(flow.device).used_test_set)
    assert {"provider": "Fast", "type": "MessageDigest", "name": "SHA-256"} in planned["include"]
    assert "SHA-256" not in (flow.tmp / "x.yaml").read_text()


def test_a_grown_used_set_runs_a_delta_not_a_rerun_and_keeps_the_record(flow):
    run(flow, flow.sha)
    runs, kept = flow.device_runs(), read_json(RunTree(flow.device).rows)["rows"]
    run(flow, flow.sha, flow.gcm)
    assert flow.device_runs() == runs and flow.ended("benchmark")[0] == "reused"
    assert len(deltas(flow)) == 1 and GCM_FAST in measured(flow)
    now = {r["rowId"]: r for r in read_json(RunTree(flow.device).rows)["rows"]}
    assert all(now[r["rowId"]]["session"] is None for r in kept)
    record, _ = rd.load_device_record(flow.device)
    assert {SHA, GCM_FAST} <= set(record.benchmark["items"]) and coverage(flow)["attempts"]["used"] == 1
    assert flow.problems() == {}


def test_the_run_after_a_delta_changes_nothing(flow):
    run(flow, flow.sha)
    run(flow, flow.sha, flow.gcm)
    before = read_yaml(RunTree(flow.device).manifest)
    run(flow, flow.sha, flow.gcm)
    assert read_yaml(RunTree(flow.device).manifest) == before and flow.ended("inbound")[0] == "reused"


def test_the_gate_stopping_makes_no_model_call(flow):
    run(flow, flow.sha)
    asked = flow.calls()
    code, _, _ = run(flow, flow.sha, flow.gcm, benchmark={"onGap": "stop"})
    assert code == 1 and flow.calls() == asked and stopped_naming(flow, GCM_FAST)
    assert flow.ended("grouping", stage="guide") == (None, {})


def test_device_results_stops_with_the_full_list_and_the_command(flow):
    run(flow, flow.sha)
    asked, runs = flow.calls(), flow.device_runs()
    code, _, _ = run(flow, flow.sha, flow.gcm, extra=("--device-results", str(flow.device)))
    assert code == 1 and flow.calls() == asked and flow.device_runs() == runs
    assert not (flow.device / "delta").exists()
    assert stopped_naming(flow, GCM_FAST)
    events = (RunTree(flow.device).log.events).read_text()
    assert "python3 -m perfrepair guide --config" in events and str(flow.device.parent) in events


def test_a_coded_gap_does_not_stop_the_guide_and_is_listed_as_missing(flow):
    run(flow, flow.sha)
    run(flow, flow.sha, flow.hmac)
    assert coverage(flow)["items"][HMAC] == "refused"
    missing = read_yaml(RunTree(flow.device).log.primitives_missing)["missing"]
    assert any(m["reason"] == "not_benchmarked" and m["provider"] == "Slow" and m["action"] == "skipped" for m in missing)
    assert flow.ended("grouping", stage="guide")[0] == "ok"


def test_filter_by_apps_off_still_runs_the_gate_on_the_measured_plan(flow, monkeypatch):
    flow.filter = False
    monkeypatch.delenv("FAKE_SELECT")
    run(flow, flow.sha)
    doc = coverage(flow)
    assert doc["point"] in ("used", "grouped") and doc["totals"]["usedItems"] > 1
    assert doc["items"]["MessageDigest|SHA-256|Slow"] == "repeats"
    assert not (RunTree(flow.device).used).exists()


def test_stops_not_benchmarked_warn_cannot_fall_through_into_a_delta(flow):
    run(flow, flow.sha)
    path = flow.settings()
    runs = flow.device_runs()
    document = yaml.safe_load(path.read_text())
    document["stops"] = {"not_benchmarked": "warn"}
    flow.settings = lambda: path.write_text(yaml.safe_dump(document)) and path
    code, _, _ = run(flow, flow.sha, flow.gcm, benchmark={"onGap": "stop"})
    assert code == 1 and flow.device_runs() == runs and not (flow.device / "delta").exists()
    assert stopped_naming(flow, GCM_FAST)


def test_a_broken_use_grows_the_used_set_by_its_upgrade_targets_and_that_runs_a_delta(flow, monkeypatch):
    md5 = "MessageDigest|MD5|Aaa"
    monkeypatch.setitem(CALLS, md5, 'java.security.MessageDigest.getInstance("MD5", "Aaa")')
    flow.add_provider()
    run(flow, flow.hmac)
    runs = flow.device_runs()
    assert SHA not in measured(flow)
    run(flow, flow.hmac, target(flow, "md5", md5, ships="g:a:1"))
    used = read_json(RunTree(flow.device).used)["items"]
    assert {u["item"]: u["via"] for u in used if u["item"] == SHA} == {SHA: "upgrade"}
    assert flow.device_runs() == runs and len(deltas(flow)) == 1 and SHA in measured(flow)
