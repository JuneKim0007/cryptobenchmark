"""The gate's partial and low_quality classes and the merge's per-case sample check, on the recorded results and the fake
pipeline; a real device run is not exercised here."""
import json
from dataclasses import replace

import pytest
import yaml
from helpers import summary
from perfrepair import run_dir as rd
from perfrepair.device.delta import _drift
from perfrepair.device.delta_config import narrowed, write_delta_config
from perfrepair.device.delta_merge import merge_delta
from perfrepair.device.measured_check import measured_check
from perfrepair.device.setup_fingerprint import differing, without_narrowed
from perfrepair.dto.benchmark_coverage import LOW_QUALITY, MEASURED, PARTIAL, Gap
from perfrepair.dto.perf_mode import GENERIC_MODE
from perfrepair.files import read_json, read_yaml
from perfrepair.stop.halt import Coded
from test_benchmark_gate import (  # noqa: F401
    GCM,
    GCM_SLOW,
    SHA,
    device,
    gate,
    rewrite,
    staged_copy,
)


def _plan_allocation(device):  # noqa: F811
    prepared = read_yaml(device / "preparation/prepared.yaml")
    for c in prepared["cases"]:
        c["metrics"] = ["TIME", "ALLOCATION"]
    (device / "preparation/prepared.yaml").write_text(yaml.safe_dump(prepared))


def test_a_partial_case_gets_only_its_missing_metric_and_keeps_its_samples(device, monkeypatch):  # noqa: F811
    _plan_allocation(device)
    monkeypatch.setenv("FAKE_METRICS", "1")
    monkeypatch.setenv("FAKE_FILL", "1")
    before = {c["id"]: c for c in read_json(device / "benchmark/benchmark.json")["cases"]}
    (coverage, merged), _ = gate(device, GCM_SLOW, perf=GENERIC_MODE)
    assert merged and coverage.items() == {GCM_SLOW: MEASURED}
    manifest = read_yaml(device / rd.MANIFEST)
    after = {c["id"]: c for c in read_json(device / manifest["files"]["benchmark"])["cases"]}
    assert after["g_slow"]["metrics"]["timeNs"] == before["g_slow"]["metrics"]["timeNs"]
    assert "allocationCount" in after["g_slow"]["metrics"] and after["g_fast"] == before["g_fast"]
    assert manifest["deltas"][0]["filled"] == {"g_slow": ["allocationCount"]}


def test_a_missing_variant_beside_a_measured_one_is_partial(device):  # noqa: F811
    prepared = read_yaml(device / "preparation/prepared.yaml")
    g_fast = next(c for c in prepared["cases"] if c["id"] == "g_fast")
    g_fast["variant"] = "notFixed"
    prepared["cases"].append({**g_fast, "id": "g_fast_fixed", "variant": "fixed"})
    (device / "preparation/prepared.yaml").write_text(yaml.safe_dump(prepared))
    seen = measured_check(device, frozenset({GCM}), GENERIC_MODE)
    [gap] = [g for g in seen.gaps if g.case == "g_fast_fixed"]
    assert gap.gap == PARTIAL and gap.variant == "fixed" and gap.reason.startswith("variant_missing")


def test_too_few_runs_is_coded_and_spends_no_delta(device):  # noqa: F811
    def one_run(doc):
        doc["cases"][2]["metrics"]["timeNs"]["runs"] = [50]
    rewrite(device, "benchmark/benchmark.json", one_run)
    (coverage, merged), lines = gate(device, SHA)
    assert not merged and coverage.items() == {SHA: LOW_QUALITY} and coverage.delta() == ()
    assert coverage.gaps[0].action == "coded" and "1 runs" in coverage.gaps[0].reason and not any(line.startswith("delta:") for line in lines)


def test_an_anchor_with_too_few_runs_checks_nothing():
    one_run = replace(summary(5.0), n=1, processes=((5.0,),))
    assert _drift({"a": {"timeNs": one_run}}, {"a": {"timeNs": summary(5.0)}}, {"a"}) == ((), 0)


def test_a_merge_refuses_a_case_with_another_sample_count(device, tmp_path):  # noqa: F811
    staged = staged_copy(device, tmp_path)
    doc = read_json(staged / "benchmark/benchmark.json")
    doc["cases"][-1]["metrics"]["timeNs"]["runs"] = [1.0] * 7
    (staged / "benchmark/benchmark.json").write_text(json.dumps(doc))
    with pytest.raises(Coded, match="unequal_samples: added.timeNs"):
        merge_delta(device, staged, {"added"}, "s", "checked")


def _added_item(device, staged, harness, stored_harness=None):  # noqa: F811
    """A case of an item the stored benchmark has no case of, planned with `harness`."""
    doc = read_json(staged / "benchmark/benchmark.json")
    doc["cases"].append({**doc["cases"][0], "id": "new", "provider": "New"})
    doc["cases"][-1]["metrics"] = {"timeNs": {**doc["cases"][0]["metrics"]["timeNs"], "runs": [1.0] * 7}}
    (staged / "benchmark/benchmark.json").write_text(json.dumps(doc))
    for folder, setup in ((device, stored_harness), (staged, stored_harness)):
        plan = read_yaml(folder / "preparation/prepared.yaml")
        plan["cases"] = [{**c, "harness": setup} for c in plan["cases"]]
        if folder == staged:
            plan["cases"].append({"id": "new", "harness": harness})
        (folder / "preparation/prepared.yaml").write_text(yaml.safe_dump(plan))


def test_a_merge_holds_a_new_items_case_to_the_stored_cases_planned_alike(device, tmp_path):  # noqa: F811
    staged = staged_copy(device, tmp_path)
    _added_item(device, staged, {"iterations": 50}, {"iterations": 50})
    with pytest.raises(Coded, match=r"unequal_samples: new\.timeNs"):
        merge_delta(device, staged, {"new"}, "s", "checked")


def test_a_merge_takes_a_new_items_own_override_of_its_samples(device, tmp_path):  # noqa: F811
    staged = staged_copy(device, tmp_path)
    _added_item(device, staged, {"iterations": 7}, {"iterations": 50})
    assert merge_delta(device, staged, {"new"}, "s", "checked").added == ("new",)


def test_a_merge_takes_another_process_file_count_by_its_cases_samples(device, tmp_path):  # noqa: F811
    staged = staged_copy(device, tmp_path)
    manifest = read_yaml(staged / rd.MANIFEST)
    manifest["files"]["processes"] = ["benchmark/benchmark.json"]
    (staged / rd.MANIFEST).write_text(yaml.safe_dump(manifest))
    with pytest.raises(Coded, match=r"unequal_samples: added\.\w+: per process"):
        merge_delta(device, staged, {"added"}, "s", "checked")


def _partial(item, metric="allocationCount", variant="notFixed"):
    return Gap(item, "ENCRYPT", variant, 128, 1024, metric, PARTIAL, "metric_missing", "c")


def test_a_partial_only_delta_narrows_passes_and_variants(device, tmp_path):  # noqa: F811
    config = tmp_path / "global.yaml"
    document = read_yaml(config)
    document["run"] = {"variants": ["fixed", "notFixed"], "passes": {"timing": {"samples": 3}, "energy": {"samples": 1},
                                                                     "allocation": {"samples": 2}}}
    config.write_text(yaml.safe_dump(document))
    run = narrowed(document["run"], (_partial(GCM_SLOW),))
    assert run == {"variants": ["notFixed"], "passes": {"timing": {"samples": 3}, "allocation": {"samples": 2}}}
    written = read_yaml(write_delta_config(config, device, {GCM_SLOW}, run))
    assert written["run"]["passes"] == run["passes"]
    assert narrowed(document["run"], (_partial(GCM_SLOW), Gap(SHA, "*", "*", None, None, "*", "lost", "x"))) is None


def test_a_narrowed_delta_differs_only_in_what_it_left_out():
    stored = {"run.variants": ["fixed", "notFixed"], "run.passes.timing.samples": 3, "run.passes.energy.samples": 1}
    now = {"run.variants": ["notFixed"], "run.passes.timing.samples": 3}
    assert differing(*without_narrowed(stored, now)) == []
    assert differing(*without_narrowed(stored, {**now, "run.passes.timing.samples": 4})) != []
    assert differing(*without_narrowed(stored, {**now, "run.variants": ["other"]})) != []
