"""The report on a hand-built device result: one checked scope, one primitive-only, one interop failure,
one kept, one rejected edit; the summary over two such apps."""
import json
import shutil
from pathlib import Path

import pytest
import yaml
from helpers import LATENCY, LATENCY_ALLOC, QUIET

from perfrepair.dto.site import (DOSSIERS_SCHEMA_VERSION, EDITS_SCHEMA_VERSION, SCOPES_SCHEMA_VERSION,
                                 SITES_SCHEMA_VERSION)
from perfrepair.files import read_json, write_json, write_text
from perfrepair.report.__main__ import main
from perfrepair.report.app_report import build_report
from perfrepair.report.markdown import report_markdown
from perfrepair.report.command import app_report, device_summary
from perfrepair.run_dir import AppPaths
from perfrepair.validation.report import validate_report
from perfrepair.validation.summary import validate_summary

F = Path(__file__).parent / "fixtures" / "report"
A, B, C, D, E = "a00000000001", "b00000000002", "c00000000003", "d00000000004", "e00000000005"
CURRENT, OPTION = "Cipher|AES/GCM/NoPadding|Slow", "Cipher|AES/GCM/NoPadding|Fast"
ESTIMATE = {"metric": "timeNs", "ratio": 0.7, "pImprove": 0.99, "n": 50, "configuration": "ENCRYPT key 128 input 1024 WARM"}


def _scope(sid, line, pattern="notFixed", reason="unknown_default"):
    return {"id": sid, "app": "shop", "file": "src/Shop.java", "line": line, "function": f"f{line}", "pattern": pattern,
            "patternReason": reason}


def make_app(run, name="shop", checked=True):
    paths = AppPaths(run, name)
    paths.root.mkdir(parents=True)
    write_json(paths.facts, {"root": str((run / f"{name}-source").resolve())})
    scopes = [_scope(s, i) for i, s in enumerate((A, B, C, D, E), 1)]
    write_json(paths.sites, {"schemaVersion": SITES_SCHEMA_VERSION, "sites": [{}] * 6})
    write_json(paths.scopes, {"schemaVersion": SCOPES_SCHEMA_VERSION, "scopes": scopes})
    write_json(paths.units, {"schemaVersion": 1, "app": name, "units": [
        {"id": "u-ab", "members": [A, B], "links": [], "sharedFunction": ["u-c"]},
        {"id": "u-c", "members": [C], "links": [], "sharedFunction": ["u-ab"]},
        {"id": "u-d", "members": [D], "links": [], "sharedFunction": []},
        {"id": "u-e", "members": [E], "links": [], "sharedFunction": []}]})
    options = [{"alias": "R1", "item": OPTION, "pins": {}, "interop": "not_run", "estimates": [ESTIMATE]}]
    write_json(paths.dossiers, {"schemaVersion": DOSSIERS_SCHEMA_VERSION, "dossiers": [{"scope": {"id": s}, "current": CURRENT, "options": options}
                                             for s in (A, B, C, E)], "noOptions": [{"scope": D, "reason": "no_alternative"}]})
    replace = {"decision": "replace", "option": OPTION, "edits": [], "risks": [], "reason": "faster"}
    write_json(paths.replacements, {"replacements": [{"scope": s, **replace} for s in (A, B, C, E)] + [
        {"scope": D, "decision": "keep", "option": None, "edits": [], "risks": [], "reason": "no_alternative"}],
        "sources": {A: "llm", B: "llm", C: "llm", E: "fallback", D: "static"}})
    write_json(paths.edits, {"schemaVersion": EDITS_SCHEMA_VERSION, "edits": [{"scope": s, "status": "applied", "reason": None, "diff": "x"} for s in (A, B, C)]
                             + [{"scope": E, "status": "rejected", "reason": "call_moved", "diff": ""}]})
    write_text(paths.harness, yaml.safe_dump({"scopes": [{"id": s} for s in (A, B, C)]}))
    if checked:
        paths.scoped_plan.parent.mkdir(parents=True)
        shutil.copy(F / "scoped-plan.yaml", paths.scoped_plan)
    return paths


def rows(doc):
    return {s["scope"]: s for s in doc["scopes"]}


@pytest.fixture(autouse=True)
def app(tmp_path):
    return make_app(tmp_path)


def test_each_scope_reports_its_steps_and_no_number(tmp_path):
    doc = app_report(tmp_path, "shop", LATENCY, **QUIET)
    r = rows(doc)
    assert r[A]["decision"] == {"decision": "replace", "reason": "faster", "source": "llm", "stale": False,
                                "needs": [], "concerns": []}
    assert (r[A]["current"], r[A]["option"], r[A]["edit"]["status"], r[A]["compile"]["status"]) == (CURRENT, OPTION, "applied",
                                                                                                 "compiled")
    assert r[A]["interop"] == {"status": "passed", "reason": None, "check": "same_output"} and r[A]["primitive"] == [ESTIMATE]
    assert r[B]["compile"] == {"status": "primitive_only", "reason": "missing_input: inputSize for in"}
    assert r[C]["interop"] == {"status": "interop_failed", "reason": "outputs_differ", "check": "same_output"}
    assert r[D]["decision"]["source"] == "static" and r[D]["edit"]["status"] == "skipped"
    assert r[E]["edit"] == {"status": "rejected", "reason": "call_moved"}
    assert not {"metrics", "verdict", "label", "thermal", "measuredBy"} & set(r[A])
    assert doc["funnel"] == {"sites": 6, "scopes": 5, "units": 4, "withOptions": 4, "recommend": 0, "replace": 4, "unitsReplace": 3,
                             "applied": 3, "compiled": 2, "interopPassed": 1}
    assert validate_report(doc, "shop") == []


def test_the_markdown_carries_the_steps_and_the_primitive_evidence(tmp_path, app):
    app_report(tmp_path, "shop", LATENCY, **QUIET)
    text = app.report_md.read_text()
    assert "- compile: primitive_only: missing_input: inputSize for in" in text
    assert "Primitive evidence" in text and "ratio 0.700, pImprove 0.99" in text


def _plan(app, change):
    plan = yaml.safe_load(app.scoped_plan.read_text())
    for record in plan["scopes"]:
        record.update(change.get(record["id"], {}))
    write_text(app.scoped_plan, yaml.safe_dump(plan))


def test_an_unchecked_or_not_comparable_interop_says_so(tmp_path, app):
    reason = "nondeterministic_output: two calls of before differ on one input"
    _plan(app, {A: {"interop": {"check": "same_output", "result": "unchecked", "reason": reason}},
                B: {"status": "not_measurable", "reason": "no_operation"},
                C: {"status": "not_comparable", "interop": {"check": "same_output", "result": "not_comparable",
                                                            "reason": "identity_only_output: X has no value equality"}}})
    r = rows(app_report(tmp_path, "shop", LATENCY, **QUIET))
    assert r[A]["interop"]["status"] == "unchecked"
    assert r[B]["compile"] == {"status": "not_measurable", "reason": "no_operation"}
    assert r[C]["interop"]["status"] == "not_comparable"
    assert f"interop: unchecked: {reason} (check same_output)" in app.report_md.read_text()


def test_without_a_device_run_nothing_is_checked(tmp_path):
    shutil.rmtree(AppPaths(tmp_path, "shop").checked)
    doc = app_report(tmp_path, "shop", LATENCY, **QUIET)
    assert rows(doc)[A]["compile"] == {"status": "not_run", "reason": "no_device_run: checked/scoped/scoped-plan.yaml absent"}
    assert doc["funnel"]["interopPassed"] == 0


def test_a_plan_of_another_harness_is_refused(tmp_path, app):
    write_text(app.harness, yaml.safe_dump({"scopes": [{"id": A}]}))
    with pytest.raises(ValueError, match="scoped_plan_mismatch"):
        app_report(tmp_path, "shop", LATENCY, **QUIET)


def test_the_validator_refuses_a_bad_row_and_a_wrong_funnel(tmp_path):
    doc = app_report(tmp_path, "shop", LATENCY, **QUIET)
    bad = json.loads(json.dumps(doc))
    rows(bad)[C]["inputs"] = {"inputSize": 1024, "keySize": None, "from": "guess"}
    assert any("inputs {'inputSize': 1024, 'keySize': None, 'from': 'guess'}" in p for p in validate_report(bad, "shop"))
    bad = json.loads(json.dumps(doc))
    bad["funnel"]["compiled"] = 3
    assert validate_report(bad, "shop") == [f"funnel {bad['funnel']} is not the recount of the scope rows"]


def test_the_summary_sums_the_funnel_and_keeps_each_apps_mode(tmp_path):
    make_app(tmp_path, "slow")
    app_report(tmp_path, "shop", LATENCY, **QUIET)
    app_report(tmp_path, "slow", LATENCY_ALLOC, **QUIET)
    doc = device_summary(tmp_path, **QUIET)
    assert doc["funnel"]["sites"] == 12 and doc["funnel"]["interopPassed"] == 2
    assert doc["modes"] == {"shop": "latency", "slow": "latency+memAlloc"}
    reports = [read_json(AppPaths(tmp_path, n).report) for n in ("shop", "slow")]
    assert validate_summary(doc, reports) == []
    assert validate_summary({**doc, "funnel": {**doc["funnel"], "sites": 1}}, reports) == ["funnel is not the sum of byApp"]
    assert validate_summary({**doc, "modes": {}}, reports) == ["modes are not each report's own"]


def test_rows_carry_the_pattern_and_the_summary_counts_each(tmp_path):
    paths = AppPaths(tmp_path, "shop")
    scopes = read_json(paths.scopes)
    for s in scopes["scopes"]:
        if s["id"] == A:
            s.update(pattern="fixed", patternReason="held_in_field")
    write_json(paths.scopes, scopes)
    r = rows(app_report(tmp_path, "shop", LATENCY, **QUIET))
    assert (r[A]["pattern"], r[A]["patternReason"]) == ("fixed", "held_in_field")
    doc = device_summary(tmp_path, **QUIET)
    assert doc["patterns"]["byApp"]["shop"] == {"fixed": 1, "notFixed": 4, "unknownDefault": 4}
    assert "| shop | 1 | 4 | 4 |" in (tmp_path / "summary.md").read_text()


def test_the_report_and_summary_name_the_project_and_source_beside_the_id(tmp_path):
    source = tmp_path / "shop-source"
    source.mkdir()
    (source / "settings.gradle.kts").write_text('rootProject.name = "Shop App"\n')
    doc = app_report(tmp_path, "shop", LATENCY, **QUIET)
    assert (doc["project"], doc["source"]) == ("Shop App", str(source.resolve()))
    assert "Project: Shop App." in AppPaths(tmp_path, "shop").report_md.read_text()
    assert device_summary(tmp_path, **QUIET)["named"]["shop"]["project"] == "Shop App"


def test_the_summary_refuses_an_empty_run(tmp_path):
    assert main(["summary", "--device-results", str(tmp_path / "empty")]) == 1


def test_the_command_writes_both_files(tmp_path, app):
    assert main(["app", "--device-results", str(tmp_path), "--app", str(tmp_path / "shop-source"), "--perf-mode", "latency,memAlloc"]) == 0
    assert read_json(app.report)["mode"] == "latency+memAlloc" and app.report_md.is_file()


def test_rows_carry_their_unit_and_the_units_their_function_shares(tmp_path):
    paths = AppPaths(tmp_path, "shop")
    doc = build_report(paths, LATENCY)
    rows = {r["scope"]: r for r in doc["scopes"]}
    assert (rows[A]["unit"], rows[B]["unit"], rows[A]["sharedFunction"]) == ("u-ab", "u-ab", ["u-c"])
    assert rows[D]["sharedFunction"] == [] and len(doc["scopes"]) == 5
    assert "- unit: u-ab; its function also holds u-c" in report_markdown(doc)


def test_a_row_names_the_members_that_stayed_while_its_unit_was_replaced(tmp_path):
    paths = AppPaths(tmp_path, "shop")
    units = read_json(paths.units)
    units["units"] = [u for u in units["units"] if u["id"] not in ("u-c", "u-d")] + [
        {"id": "u-cd", "members": [C, D], "links": [], "sharedFunction": []}]
    write_json(paths.units, units)
    doc = build_report(paths, LATENCY)
    rows = {r["scope"]: r for r in doc["scopes"]}
    assert rows[C]["stayed"] == rows[D]["stayed"] == [D] and rows[A]["stayed"] == [] and rows[E]["stayed"] == []
    assert validate_report(doc, "shop") == []
    assert any("stayed" in p for p in validate_report({**doc, "scopes": [{**rows[A], "stayed": [D]}, *doc["scopes"][1:]]}, "shop"))
    assert f"- unit: u-cd; stayed on what they use: {D}" in report_markdown(doc)


def test_a_blocked_member_says_which_member_rejected_the_unit(tmp_path):
    paths = AppPaths(tmp_path, "shop")
    edits = read_json(paths.edits)
    for row in edits["edits"]:
        if row["scope"] == A:
            row.update(status="rejected", reason="unit_member_rejected", diff="", blockedBy=f"{B}: call_moved")
    write_json(paths.edits, edits)
    row = next(r for r in build_report(paths, LATENCY)["scopes"] if r["scope"] == A)
    assert row["edit"] == {"status": "rejected", "reason": f"unit_member_rejected: {B}: call_moved"}


def test_a_report_without_units_says_which_step_to_run(tmp_path):
    paths = AppPaths(tmp_path, "shop")
    paths.units.unlink()
    with pytest.raises(ValueError, match="missing_step"):
        build_report(paths, LATENCY)
