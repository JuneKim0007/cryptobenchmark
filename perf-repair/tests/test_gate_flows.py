"""The benchmark gate through the guide, on the fake pipeline and the dry-run gateway: the used set adding what the test set
lacks, a delta between runs, the stop before any model call. No real device or model is exercised."""
import pytest
import yaml

from perfrepair import run_dir as rd
from perfrepair.files import read_json, read_yaml
from perfrepair.guide.command import main as guide
from test_device_flows import CALLS, GCM_FAST, HMAC, SHA, Flow, F, target

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
    document["run"] = {"onExisting": "resume"}
    document["device"]["benchmark"].update(benchmark or {})
    path.write_text(yaml.safe_dump(document))
    code = guide(["--agent", "dry-run", "--perfrepair-config", str(path), *extra])
    captured = flow.capsys.readouterr()
    return code, captured.out.splitlines(), captured.err


def measured(flow):
    return {f"{r['type']}|{r['algorithm']}|{r['provider']}" for r in read_json(flow.device / rd.ROWS)["rows"]}


def coverage(flow):
    return read_yaml(flow.device / rd.BENCHMARK_COVERAGE)


def test_a_used_item_outside_the_test_set_is_planned_and_measured(flow):
    _, lines, _ = run(flow, flow.sha)
    assert SHA in measured(flow) and coverage(flow)["items"] == {SHA: "measured"}
    planned = read_yaml(flow.device / rd.USED_TEST_SET)
    assert {"provider": "Fast", "type": "MessageDigest", "name": "SHA-256"} in planned["include"]
    assert "SHA-256" not in (flow.tmp / "x.yaml").read_text()
    assert any(line.startswith("device gate (used): 1 of 1 used items measured") for line in lines)


def test_a_grown_used_set_runs_a_delta_not_a_rerun_and_keeps_the_record(flow):
    run(flow, flow.sha)
    runs, kept = flow.device_runs(), read_json(flow.device / rd.ROWS)["rows"]
    _, lines, _ = run(flow, flow.sha, flow.gcm)
    assert flow.device_runs() == runs and "device benchmark: reused" in lines
    assert any(line.startswith("delta:     ") for line in lines) and GCM_FAST in measured(flow)
    now = {r["rowId"]: r for r in read_json(flow.device / rd.ROWS)["rows"]}
    assert all(now[r["rowId"]]["session"] is None for r in kept)
    record, _ = rd.load_device_record(flow.device)
    assert {SHA, GCM_FAST} <= set(record.benchmark["items"]) and coverage(flow)["attempts"]["used"] == 1
    assert flow.problems() == {}


def test_the_run_after_a_delta_changes_nothing(flow):
    run(flow, flow.sha)
    run(flow, flow.sha, flow.gcm)
    before = read_yaml(flow.device / rd.MANIFEST)
    _, lines, _ = run(flow, flow.sha, flow.gcm)
    assert read_yaml(flow.device / rd.MANIFEST) == before and "device inbound: reused" in lines
    assert not any(line.startswith("delta:     ") for line in lines)


def test_the_gate_stopping_makes_no_model_call(flow):
    run(flow, flow.sha)
    asked = flow.calls()
    code, lines, err = run(flow, flow.sha, flow.gcm, benchmark={"onGap": "stop"})
    assert code == 1 and flow.calls() == asked
    assert any(line.startswith("guide prerequisites: stop not_benchmarked") and GCM_FAST in line for line in lines)
    assert not any(line.startswith("guide grouping") for line in lines)


def test_device_results_stops_with_the_full_list_and_the_command(flow):
    run(flow, flow.sha)
    asked, runs = flow.calls(), flow.device_runs()
    code, lines, _ = run(flow, flow.sha, flow.gcm, extra=("--device-results", str(flow.device)))
    assert code == 1 and flow.calls() == asked and flow.device_runs() == runs
    assert not (flow.device / "delta").exists()
    assert GCM_FAST in next(line for line in lines if line.startswith("guide prerequisites: stop not_benchmarked"))
    events = (flow.device / rd.EVENTS).read_text()
    assert "python3 -m perfrepair guide --config" in events and str(flow.device.parent) in events


def test_a_coded_gap_does_not_stop_the_guide_and_is_listed_as_missing(flow):
    run(flow, flow.sha)
    _, lines, _ = run(flow, flow.sha, flow.hmac)
    assert coverage(flow)["items"][HMAC] == "refused"
    missing = read_yaml(flow.device / rd.PRIMITIVES_MISSING)["missing"]
    assert any(m["reason"] == "not_benchmarked" and m["provider"] == "Slow" and m["action"] == "skipped" for m in missing)
    assert any(line.startswith("guide grouping: ok") for line in lines)


def test_after_a_delta_replace_asks_changed_dossiers_again_and_never_stops_on_them(monkeypatch):
    from dataclasses import replace as with_fields

    from perfrepair.guide import app_steps
    from perfrepair.guide.state import Guide
    seen = {}

    def replaced(*_, refresh, **__):
        seen["refresh"] = refresh
        raise SystemExit
    monkeypatch.setattr(app_steps, "replace", replaced)
    base = Guide(F, F, None, None, None)
    for merged in (False, True):
        with pytest.raises(SystemExit):
            app_steps.replacements(with_fields(base, app_root=F, delta_merged=merged))
        assert seen["refresh"] is merged
