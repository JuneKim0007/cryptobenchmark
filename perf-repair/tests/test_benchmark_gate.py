"""The benchmark gate on the recorded results and the fake pipeline: one gap class per test, the setup fingerprint, the
delta's merge and anchors; a real device run is not exercised here."""
import json
from pathlib import Path

import pytest
import yaml

from helpers import TIMING, with_results
from perfrepair import run_dir as rd
from perfrepair.device import delta_merge
from perfrepair.device.delta_estimate import seconds_per_case
from perfrepair.device.delta_merge import merge_delta
from perfrepair.device.gate import GatePolicy, benchmark_gate
from perfrepair.device.inbound import write_inbound
from perfrepair.device.measured_check import measured_check
from perfrepair.device.setup_fingerprint import case_setups, differing, fingerprint
from perfrepair.dto.benchmark_coverage import (
    LOST,
    MEASURED,
    NEVER_PLANNED,
    NO_OPERATION,
    PARTIAL,
    REFUSED,
    REPEATS,
)
from perfrepair.dto.perf_mode import GENERIC_MODE
from perfrepair.dto.used import UsedItem, UsedSet
from perfrepair.files import read_json, read_yaml
from perfrepair.grouping.build.stage import build_stage
from perfrepair.result.configurations import Config, cross_session
from perfrepair.screen.catalog import screening_catalog
from perfrepair.stop import Halt
from perfrepair.stop.halt import Coded

F = Path(__file__).parent / "fixtures"
FOLDER = "fake-api36-00000000"
GCM, GCM_SLOW = "Cipher|AES/GCM/NoPadding|Fast", "Cipher|AES/GCM/NoPadding|Slow"
SHA, SHA_LOST = "MessageDigest|SHA-256|Fast", "MessageDigest|SHA-256|Slow"
HMAC = "Mac|HmacSHA256|Slow"


@pytest.fixture
def device(tmp_path, monkeypatch):
    """The recorded benchmark as a stored folder, with its config beside it and the fake pipeline as the benchmark."""
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(F / "device"))
    monkeypatch.setenv("FAKE_DEVICE_ID", FOLDER)
    (tmp_path / "set.yaml").write_text("schemaVersion: 1\ninclude: [{type: Cipher}]\n")
    config = tmp_path / "global.yaml"
    config.write_text("schemaVersion: 1\nselection: {testSet: set.yaml}\nproviders: {bundled: []}\n")
    folder = with_results(tmp_path / "results" / FOLDER)
    manifest = read_yaml(folder / rd.MANIFEST)
    manifest.update(deviceId=FOLDER, config=str(config))
    del manifest["retried"]
    (folder / rd.MANIFEST).write_text(yaml.safe_dump(manifest, sort_keys=False))
    # the recorded lost case's item: the probe holds it, so a delta's row has a verdict
    path = folder / manifest["files"]["probe"]
    probe = read_yaml(path)
    probe["providers"][1]["services"].append({"type": "MessageDigest", "algorithm": "SHA-256", "className": "b.D"})
    path.write_text(yaml.safe_dump(probe, sort_keys=False))
    trial = read_yaml(folder / manifest["files"]["trial"])
    trial["services"].append({"provider": "Slow", "type": "MessageDigest", "algorithm": "SHA-256", "instantiates": True,
                              "defaultRun": {"works": True, "inputSize": 1024}})
    (folder / manifest["files"]["trial"]).write_text(yaml.safe_dump(trial, sort_keys=False))
    inventory = read_yaml(folder / manifest["files"]["inventory"])
    inventory["providers"]["Slow"]["MessageDigest"] = {"SHA-256": {"runs": True}}
    (folder / manifest["files"]["inventory"]).write_text(yaml.safe_dump(inventory, sort_keys=False))
    write_inbound(folder)
    build_stage(folder / rd.MANIFEST, folder, screening_catalog(None), echo=lambda _: None)
    return folder


def used(*items):
    return UsedSet(9, {}, tuple(UsedItem(i, "site", ("a",)) for i in items))


def check(folder, *items, perf=TIMING):
    return measured_check(folder, frozenset(items), perf)


def rewrite(folder, name, change):
    doc = json.loads((folder / name).read_text())
    change(doc)
    (folder / name).write_text(json.dumps(doc))
    write_inbound(folder)


def test_every_planned_key_with_enough_runs_is_measured(device):
    seen = check(device, GCM)
    assert seen.items() == {GCM: MEASURED} and seen.gaps == () and seen.measured == 1


def test_a_used_item_nothing_plans_is_never_planned(device):
    assert check(device, "KeyGenerator|HmacX|Fast").items() == {"KeyGenerator|HmacX|Fast": NEVER_PLANNED}


def test_a_planned_case_without_rows_is_lost_once_then_repeats(device):
    first = check(device, SHA_LOST)
    assert first.items() == {SHA_LOST: LOST} and first.gaps[0].case == "d_slow" and first.gaps[0].action == "delta"
    manifest = read_yaml(device / rd.MANIFEST)
    (device / rd.MANIFEST).write_text(yaml.safe_dump({**manifest, "retried": ["d_slow"]}, sort_keys=False))
    again = check(device, SHA_LOST)
    assert again.items() == {SHA_LOST: REPEATS} and again.delta() == () and again.gaps[0].action == "coded"


def test_a_provider_refusal_from_the_run_log_is_coded_and_keeps_its_reason(device):
    seen = check(device, HMAC)
    assert seen.items() == {HMAC: REFUSED} and seen.delta() == () and "BadKey" in seen.gaps[0].reason


def test_a_metric_the_case_planned_and_lacks_is_partial(device):
    prepared = read_yaml(device / "preparation/prepared.yaml")
    for c in prepared["cases"]:
        c["metrics"] = ["TIME", "ALLOCATION"]
    (device / "preparation/prepared.yaml").write_text(yaml.safe_dump(prepared))
    seen = check(device, GCM_SLOW, perf=GENERIC_MODE)
    assert seen.items() == {GCM_SLOW: PARTIAL} and seen.gaps[0].metric == "allocationCount" and seen.measured == 1


def test_the_operations_come_from_the_benchmarks_manifest(device):
    manifest = read_yaml(device / rd.MANIFEST)
    (device / rd.MANIFEST).write_text(yaml.safe_dump({**manifest, "operations": {"Cipher": ["ENCRYPT"]}}, sort_keys=False))
    assert check(device, SHA).items() == {SHA: NO_OPERATION} and check(device, GCM).items() == {GCM: MEASURED}


def test_a_type_with_no_harness_operation_is_coded_from_the_harness_list(device):
    seen = check(device, "SecureRandom|X|Fast")
    assert seen.items() == {"SecureRandom|X|Fast": NO_OPERATION} and seen.delta() == ()
    assert seen.gaps[0].reason.startswith("no_harness_operation")


@pytest.mark.parametrize("field, edit", [
    ("deviceId", lambda m, e: m.update(deviceId="other")),
    ("runtime.fingerprint", lambda m, e: m["runtime"].update(fingerprint="other")),
    ("runtime.compilationMode", lambda m, e: m["runtime"].update(compilationMode="quicken")),
    ("processes", lambda m, e: m["files"].update(processes=["benchmark/benchmark.json"])),
    ("energy", lambda m, e: m.update(energy={"source": "manafa", "kind": "estimated"})),
    ("run.harness.energy.capture", lambda m, e: e["run"].update(harness={"energy": {"capture": "measured"}})),
    ("run.seed", lambda m, e: e["run"].update(seed=9)),
    ("run.inputSizes", lambda m, e: e["run"].update(inputSizes=[1])),
    ("run.harness.iterations", lambda m, e: e["run"].update(harness={"iterations": 2})),
    ("run.passes.timing.samples", lambda m, e: e["run"].update(passes={"timing": {"samples": 3}})),
    ("run.thermalGate.marginCelsius", lambda m, e: e["run"].update(thermalGate={"marginCelsius": 9})),
])
def test_a_setup_field_that_differs_is_named(device, field, edit):
    stored = fingerprint(device)
    manifest, effective = read_yaml(device / rd.MANIFEST), read_yaml(device / "configuration/effective.yaml")
    edit(manifest, effective)
    (device / rd.MANIFEST).write_text(yaml.safe_dump(manifest))
    (device / "configuration/effective.yaml").write_text(yaml.safe_dump(effective))
    assert any(line.startswith(f"{field}:") for line in differing(stored, fingerprint(device)))


def test_a_new_bundled_provider_differs(device):
    stored = fingerprint(device)
    path = device / read_yaml(device / rd.MANIFEST)["files"]["probe"]
    probe = read_yaml(path)
    probe["providers"].append({"name": "New", "version": "1", "origin": "bundled", "artifact": "g:a:1", "services": []})
    path.write_text(yaml.safe_dump(probe))
    assert [line.split(":")[0] for line in differing(stored, fingerprint(device))] == ["bundled"]


def test_an_override_reaching_a_case_differs(device):
    stored = case_setups(device)
    prepared = read_yaml(device / "preparation/prepared.yaml")
    prepared["cases"][0]["resolvedParameters"] = {"tagBits": 96}
    (device / "preparation/prepared.yaml").write_text(yaml.safe_dump(prepared))
    assert any("resolvedParameters" in line for line in differing(stored["g_fast"], case_setups(device)["g_fast"]))


def gate(folder, *items, policy=GatePolicy(), perf=TIMING):
    lines = []
    return benchmark_gate(folder, "used", used(*items), perf, policy, True, lines.append, F / "device"), lines


def test_a_lost_case_is_measured_once_merged_and_the_benchmark_keeps_its_rows(device, monkeypatch):
    monkeypatch.setenv("FAKE_HEAL", "1")
    before = {c["id"] for c in read_json(device / "benchmark/benchmark.json")["cases"]}
    (coverage, merged), lines = gate(device, GCM, SHA_LOST)
    assert merged and coverage.items() == {GCM: MEASURED, SHA_LOST: MEASURED}
    manifest = read_yaml(device / rd.MANIFEST)
    cases = {c["id"]: c for c in read_json(device / manifest["files"]["benchmark"])["cases"]}
    assert set(cases) == before | {"d_slow"} and cases["d_slow"]["session"] == manifest["deltas"][0]["session"]
    assert "session" not in cases["g_fast"] and any(line.startswith("delta:     ") for line in lines)
    assert {r.rowId: r.session for r in rd.load_rows(device)}["d_slow"] == manifest["deltas"][0]["session"]
    doc = read_yaml(device / rd.BENCHMARK_COVERAGE)
    assert doc["attempts"] == {"used": 1} and doc["deltas"][0]["added"] == ["d_slow"] and doc["totals"]["gaps"] == 0


def test_a_lost_case_lost_again_repeats_and_does_not_stop(device):
    (coverage, merged), _ = gate(device, SHA_LOST)
    assert merged and coverage.items() == {SHA_LOST: REPEATS} and coverage.delta() == ()


def test_on_gap_stop_measures_nothing_and_lists_every_gap(device):
    with pytest.raises(Halt) as e:
        gate(device, SHA_LOST, "KeyGenerator|HmacX|Fast", policy=GatePolicy(on_gap="stop"))
    assert e.value.code == "not_benchmarked" and "KeyGenerator|HmacX|Fast" in e.value.detail and SHA_LOST in e.value.detail
    assert "deltas" not in read_yaml(device / rd.MANIFEST)


def test_device_results_stops_with_the_exact_command(device):
    with pytest.raises(Halt) as e:
        gate(device, SHA_LOST, policy=GatePolicy(command="`python3 -m perfrepair guide --config x`"))
    assert e.value.code == "not_benchmarked" and e.value.next_step == "`python3 -m perfrepair guide --config x`"
    assert "run `python3 -m perfrepair guide --config x`" in e.value.detail
    assert not (device / "delta").exists()


def test_a_coded_gap_alone_starts_no_delta_and_does_not_stop(device):
    (coverage, merged), _ = gate(device, HMAC, "SecureRandom|X|Fast")
    assert not merged and len(coverage.coded()) == 2 and not (device / "delta").exists()


def test_a_setup_that_differs_refuses_the_delta_naming_the_field(device, monkeypatch):
    monkeypatch.setenv("FAKE_FINGERPRINT", "another-build")
    before = (device / rd.MANIFEST).read_bytes()
    with pytest.raises(Halt) as e:
        gate(device, SHA_LOST)
    assert e.value.code == "setup_mismatch" and "runtime.fingerprint" in e.value.detail
    assert (device / rd.MANIFEST).read_bytes() == before


def test_a_setup_that_differs_is_refused_before_the_measuring_session(device, monkeypatch):
    monkeypatch.setenv("FAKE_FINGERPRINT", "another-build")
    manifest = read_yaml(device / rd.MANIFEST)
    manifest["runtime"]["fingerprint"] = "the-stored-build"
    (device / rd.MANIFEST).write_text(yaml.safe_dump(manifest, sort_keys=False))
    with pytest.raises(Halt):
        gate(device, SHA_LOST)
    # only the probe ran: its manifest lists no benchmark
    assert "benchmark" not in read_yaml(device / "delta/results" / FOLDER / rd.MANIFEST)["files"]


def test_on_setup_mismatch_rerun_measures_the_whole_benchmark_with_the_gap_added(device, monkeypatch):
    monkeypatch.setenv("FAKE_FINGERPRINT", "another-build")
    monkeypatch.setenv("FAKE_HEAL", "1")
    (coverage, merged), lines = gate(device, SHA_LOST, policy=GatePolicy(on_mismatch="rerun"))
    assert merged and coverage.items() == {SHA_LOST: MEASURED} and any("the whole benchmark" in line for line in lines)
    manifest = read_yaml(device / rd.MANIFEST)
    assert manifest["runtime"]["fingerprint"] == "another-build" and manifest["deltas"][0]["rerun"] is True


def test_the_estimate_ignores_a_delta_call_and_counts_the_whole_run(tmp_path):
    logs = tmp_path / rd.PIPELINE_LOGS
    logs.mkdir(parents=True)
    (logs / "a.log").write_text("# bench\n$ pipeline --results /r\ntook:      prepare and measure in 80.0s\n"
                                "# bench\n$ pipeline --results /r/d/delta/results\ntook:      prepare and measure in 2.0s\n")
    assert seconds_per_case(tmp_path, 40) == 2.0


def test_another_device_connected_is_refused_before_the_delta(device, monkeypatch):
    monkeypatch.setenv("FAKE_DEVICE_ID", "another-device")
    with pytest.raises(Coded, match="device_id_changed"):
        gate(device, SHA_LOST)
    assert not (device / "delta").exists()


def test_anchors_that_drift_mark_the_delta_setup_drift_and_its_estimates_are_not_sent(device, monkeypatch):
    monkeypatch.setenv("FAKE_HEAL", "1")
    monkeypatch.setenv("FAKE_SCALE", "3")
    (_, merged), lines = gate(device, GCM, SHA, SHA_LOST)
    assert merged and any("setup_drift" in line and "d_fast" in line for line in lines)
    rows = {r.rowId: r for r in rd.load_rows(device)}
    assert rows["d_slow"].drift and not rows["d_fast"].drift
    assert read_yaml(device / rd.MANIFEST)["deltas"][0]["comparison"] == "setup_drift"


def test_anchors_that_agree_leave_the_delta_undrifted(device, monkeypatch):
    monkeypatch.setenv("FAKE_HEAL", "1")
    (_, merged), lines = gate(device, SHA, SHA_LOST)
    assert merged and not any("setup_drift" in line for line in lines)
    assert not {r.rowId: r for r in rd.load_rows(device)}["d_slow"].drift


def test_a_delta_with_no_anchor_is_unchecked_and_says_why(device, monkeypatch):
    monkeypatch.setenv("FAKE_HEAL", "1")
    monkeypatch.setenv("FAKE_SELECT", "1")
    (_, merged), lines = gate(device, SHA_LOST)
    assert merged and any(line.startswith("device gate: unchecked:") and "no anchor" in line for line in lines)
    assert read_yaml(device / rd.MANIFEST)["deltas"][0]["comparison"] == "unchecked"
    assert read_yaml(device / rd.BENCHMARK_COVERAGE)["deltas"][0]["comparison"] == "unchecked"
    assert any("unchecked" in line and "drifted, unchecked" in line for line in lines)
    rows = {r.rowId: r for r in rd.load_rows(device)}
    config = Config("digest", None, 1024, None)
    assert not rows["d_slow"].drift and cross_session([config], {config: rows["d_fast"]}, {config: rows["d_slow"]})


def test_anchors_whose_cases_the_overrides_changed_leave_the_delta_unchecked(device, monkeypatch):
    monkeypatch.setenv("FAKE_HEAL", "1")
    monkeypatch.setenv("FAKE_RENAME_CASES", "1")
    (_, merged), lines = gate(device, SHA, SHA_LOST)
    assert merged and any(line.startswith("device gate: unchecked:") and "overrides" in line for line in lines)
    assert read_yaml(device / rd.MANIFEST)["deltas"][0]["comparison"] == "unchecked"


def test_a_delta_on_a_host_says_drift_is_unreliable_there(device, monkeypatch):
    monkeypatch.setenv("FAKE_HEAL", "1")
    manifest = read_yaml(device / rd.MANIFEST)
    (device / rd.MANIFEST).write_text(yaml.safe_dump({**manifest, "mode": "host"}, sort_keys=False))
    lines = []
    benchmark_gate(device, "used", used(SHA, SHA_LOST), TIMING, GatePolicy(), False, lines.append, F / "device")
    assert any("drift is unreliable on a host" in line for line in lines if line.startswith("device gate (used): delta"))


def staged_copy(device, tmp_path):
    staged = tmp_path / "staged" / FOLDER
    staged.parent.mkdir()
    import shutil
    shutil.copytree(device, staged)
    doc = read_json(staged / "benchmark/benchmark.json")
    doc["cases"].append({**doc["cases"][0], "id": "added"})
    (staged / "benchmark/benchmark.json").write_text(json.dumps(doc))
    return staged


def test_a_merge_refuses_an_id_the_benchmark_holds(device, tmp_path):
    with pytest.raises(Coded, match="merge_refused"):
        merge_delta(device, staged_copy(device, tmp_path), {"g_fast"}, "s", "checked")


def test_an_interrupted_merge_leaves_the_stored_benchmark_whole(device, tmp_path, monkeypatch):
    before = {name: (device / name).read_bytes() for name in (rd.MANIFEST, "benchmark/benchmark.json", "preparation/prepared.yaml")}
    real = delta_merge.write_text_making_parents

    def dies_at_the_switch(path, text):
        if Path(path).name == rd.MANIFEST:
            raise KeyboardInterrupt
        return real(path, text)
    monkeypatch.setattr(delta_merge, "write_text_making_parents", dies_at_the_switch)
    with pytest.raises(KeyboardInterrupt):
        merge_delta(device, staged_copy(device, tmp_path), {"added"}, "s", "checked")
    assert {name: (device / name).read_bytes() for name in before} == before
    write_inbound(device)
    assert "added" not in {r.rowId for r in rd.load_rows(device)}


def test_a_merge_adds_only_and_the_folder_reads_back(device, tmp_path):
    merged = merge_delta(device, staged_copy(device, tmp_path), {"added"}, "s", "checked")
    write_inbound(device)
    assert merged.added == ("added",) and {"g_fast", "added"} <= {r.rowId for r in rd.load_rows(device)}
    assert (device / "benchmark/benchmark.json").is_file()
