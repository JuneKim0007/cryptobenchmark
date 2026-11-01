"""The report on a hand-built device result: one measured scope, one primitive-only, one interop failure,
one kept, one rejected edit; the summary over two such apps."""
import json
import shutil
from pathlib import Path

import pytest
import yaml
from helpers import QUIET

from perfrepair.files import read_json, write_json, write_text
from perfrepair.report.__main__ import main
from perfrepair.report.command import app_report, run_summary
from perfrepair.result.modes import MODES
from perfrepair.run_dir import AppPaths
from perfrepair.validation.report import validate_report, validate_summary

F = Path(__file__).parent / "fixtures" / "report"
A, B, C, D, E = "a00000000001", "b00000000002", "c00000000003", "d00000000004", "e00000000005"
CURRENT, OPTION = "Cipher|AES/GCM/NoPadding|Slow", "Cipher|AES/GCM/NoPadding|Fast"
ESTIMATE = {"metric": "timeNs", "ratio": 0.7, "pImprove": 0.99, "n": 50, "configuration": "ENCRYPT key 128 input 1024 WARM"}


def _scope(sid, line):
    return {"id": sid, "app": "shop", "file": "src/Shop.java", "line": line, "function": f"f{line}"}


def make_app(run, name="shop", after_scale=1.0, measured=True):
    paths = AppPaths(run, name)
    paths.root.mkdir(parents=True)
    scopes = [_scope(s, i) for i, s in enumerate((A, B, C, D, E), 1)]
    write_json(paths.sites, {"sites": [{}] * 6})
    write_json(paths.scopes, {"scopes": scopes})
    options = [{"alias": "R1", "item": OPTION, "pins": {}, "interop": "not_run", "estimates": [ESTIMATE]}]
    write_json(paths.dossiers, {"dossiers": [{"scope": {"id": s}, "current": CURRENT, "options": options}
                                             for s in (A, B, C, E)], "noOptions": [{"scope": D, "reason": "no_alternative"}]})
    replace = {"decision": "replace", "option": OPTION, "edits": [], "risks": [], "reason": "faster"}
    write_json(paths.replacements, {"replacements": [{"scope": s, **replace} for s in (A, B, C, E)] + [
        {"scope": D, "decision": "keep", "option": None, "edits": [], "risks": [], "reason": "no_alternative"}],
        "sources": {A: "llm", B: "llm", C: "llm", E: "fallback", D: "static"}})
    write_json(paths.edits, {"edits": [{"scope": s, "status": "applied", "reason": None, "diff": "x"} for s in (A, B, C)]
                             + [{"scope": E, "status": "rejected", "reason": "call_moved", "diff": ""}]})
    write_text(paths.harness, yaml.safe_dump({"scopes": [{"id": s} for s in (A, B, C)]}))
    if measured:
        paths.scoped_plan.parent.mkdir(parents=True)
        shutil.copy(F / "scoped-plan.yaml", paths.scoped_plan)
        bench = read_json(F / "benchmark.json")
        for case in bench["cases"]:
            if case["id"].endswith(":after"):
                case["metrics"]["timeNs"]["runs"] = [v * after_scale for v in case["metrics"]["timeNs"]["runs"]]
        write_json(paths.scoped_benchmark, bench)
    return paths


def rows(doc):
    return {s["scope"]: s for s in doc["scopes"]}


def test_a_measured_scope_reports_before_after_per_metric(tmp_path):
    doc = app_report(tmp_path, "shop", MODES["latency"], **QUIET)
    a = rows(doc)[A]
    assert a["decision"] == {"decision": "replace", "reason": "faster", "source": "llm"}
    assert (a["current"], a["option"], a["edit"]["status"], a["compile"]["status"]) == (CURRENT, OPTION, "applied",
                                                                                        "compiled")
    assert a["interop"] == {"status": "passed", "reason": None, "check": "same_output"}
    time, alloc, energy = a["metrics"]
    assert (time["before"], time["after"], time["ratio"], time["level"]) == (1000, 800, 0.8, "ok")
    assert time["throughput"]["opsPerSecond"] == {"before": 1e6, "after": 1.25e6}
    assert time["throughput"]["mbPerSecond"] == {"before": 1024.0, "after": 1280.0}
    assert (alloc["ratio"], alloc["level"]) == (1.0, "weak")
    assert (energy["before"], energy["after"], energy["pImprove"], energy["level"]) == (0.002, 0.0015, None, "too_few_runs")
    assert a["verdict"] == "improves" and a["primitive"] == [ESTIMATE]


@pytest.fixture(autouse=True)
def app(tmp_path):
    return make_app(tmp_path)


def test_every_unmeasured_scope_says_why_and_shows_no_number(tmp_path):
    doc = app_report(tmp_path, "shop", MODES["latency"], **QUIET)
    r = rows(doc)
    assert r[B]["compile"] == {"status": "primitive_only", "reason": "missing_input: inputSize for in"}
    assert r[C]["interop"] == {"status": "interop_failed", "reason": "outputs_differ", "check": "same_output"}
    assert r[D]["decision"]["source"] == "static" and r[D]["edit"]["status"] == "skipped"
    assert r[E]["edit"] == {"status": "rejected", "reason": "call_moved"}
    reasons = {s: r[s]["metrics"][0]["reason"] for s in (B, C, D, E)}
    assert reasons == {B: "primitive_only: missing_input: inputSize for in", C: "interop_failed: outputs_differ",
                       D: "not replaced: keep (no_alternative)", E: "rejected: call_moved"}
    assert all(set(m) == {"metric", "unit", "measured", "reason"} for s in (B, C, D, E) for m in r[s]["metrics"])
    assert doc["funnel"] == {"sites": 6, "scopes": 5, "withOptions": 4, "replace": 4, "applied": 3, "compiled": 2,
                             "interopPassed": 1, "measured": 1}


def test_the_markdown_carries_the_numbers_and_the_reasons(tmp_path, app):
    app_report(tmp_path, "shop", MODES["latency"], **QUIET)
    text = app.report_md.read_text()
    assert "| timeNs (ns/op) | 1,000 → 800 | 0.800 |" in text and "| MB/s | 1,024 → 1,280 |" in text
    assert "| energyJ (J/op) | 0.002 → 0.0015 | 0.750 | n/a (n<2) | 1 |" in text
    assert "not measured: primitive_only: missing_input: inputSize for in" in text
    assert "Primitive-only evidence" in text and "ratio 0.700, pImprove 0.99" in text


def test_without_a_device_run_nothing_is_measured(tmp_path):
    shutil.rmtree(AppPaths(tmp_path, "shop").measured)
    doc = app_report(tmp_path, "shop", MODES["latency"], **QUIET)
    a = rows(doc)[A]
    assert a["compile"] == {"status": "not_run", "reason": "no_device_run: measured/scoped/scoped-plan.yaml absent"}
    assert doc["measuredFrom"] is None and doc["funnel"]["measured"] == 0


def test_a_plan_of_another_harness_is_refused(tmp_path, app):
    write_text(app.harness, yaml.safe_dump({"scopes": [{"id": A}]}))
    with pytest.raises(ValueError, match="measured_mismatch"):
        app_report(tmp_path, "shop", MODES["latency"], **QUIET)


def test_the_validator_refuses_an_invented_number(tmp_path):
    doc = app_report(tmp_path, "shop", MODES["latency"], **QUIET)
    bad = json.loads(json.dumps(doc))
    rows(bad)[B]["metrics"][0] = {**rows(bad)[A]["metrics"][0]}
    rows(bad)[A]["metrics"][0]["ratio"] = 0.5
    problems = validate_report(bad, "shop")
    assert any("measured although interop is skipped" in p for p in problems)
    assert any("ratio 0.5 is not after ÷ before" in p for p in problems)
    bad = json.loads(json.dumps(doc))
    bad["funnel"]["measured"] = 2
    assert validate_report(bad, "shop") == [f"funnel {bad['funnel']} is not the recount of the scope rows"]


def test_the_summary_counts_apps_per_metric_and_sums_the_funnel(tmp_path):
    make_app(tmp_path, "slow", after_scale=1.5)
    for name in ("shop", "slow"):
        app_report(tmp_path, name, MODES["latency"], **QUIET)
    doc = run_summary(tmp_path, **QUIET)
    time = doc["metrics"]["timeNs"]
    assert time["apps"] == {"improved": ["shop"], "unchanged": [], "worse": ["slow"], "notMeasured": []}
    assert time["medianChange"] == pytest.approx(0.0)
    assert doc["metrics"]["allocationCount"]["apps"]["unchanged"] == ["shop", "slow"]
    assert doc["funnel"]["sites"] == 12 and doc["funnel"]["measured"] == 2
    text = (tmp_path / "apps" / "summary.md").read_text()
    assert "| timeNs (ns/op) | 1 | 0 | 1 | 0 | +0.0% |" in text
    reports = [read_json(AppPaths(tmp_path, n).report) for n in ("shop", "slow")]
    assert validate_summary(doc, reports) == []
    assert validate_summary({**doc, "funnel": {**doc["funnel"], "sites": 1}}, reports) == ["funnel is not the sum of byApp"]


def test_the_summary_refuses_mixed_modes_and_an_empty_run(tmp_path):
    make_app(tmp_path, "slow")
    app_report(tmp_path, "shop", MODES["latency"], **QUIET)
    app_report(tmp_path, "slow", MODES["battery"], **QUIET)
    with pytest.raises(ValueError, match="mixed_modes"):
        run_summary(tmp_path, **QUIET)
    assert main(["summary", "--run", str(tmp_path / "empty")]) == 1


def test_the_command_writes_both_files(tmp_path, app):
    assert main(["app", "--run", str(tmp_path), "--app", "shop", "--mode", "battery"]) == 0
    assert read_json(app.report)["mode"] == "battery" and app.report_md.is_file()
