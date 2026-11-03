import pathlib, sys

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import scope_results  # noqa: E402

PLAN = {"schemaVersion": 1, "app": "fixture", "seed": 7, "scopes": [
    {"id": "aaaaaaaaaaaa", "function": "f", "inputs": {"inputSize": 64, "keySize": None}, "status": "compiled",
     "interop": {"check": "same_output"}, "cases": ["scope:aaaaaaaaaaaa:before", "scope:aaaaaaaaaaaa:after"]},
    {"id": "bbbbbbbbbbbb", "function": "g", "inputs": {"inputSize": 64, "keySize": None}, "status": "compiled",
     "interop": {"check": "same_output"}, "cases": ["scope:bbbbbbbbbbbb:before", "scope:bbbbbbbbbbbb:after"]},
    {"id": "cccccccccccc", "function": "h", "status": "not_compilable", "reason": "unsupported_parameter: c: Context"},
]}


def files(tmp_path, interop):
    plan, verdicts = tmp_path / "scoped-plan.yaml", tmp_path / "scoped-interop.yaml"
    plan.write_text(yaml.safe_dump(PLAN))
    verdicts.write_text(interop)
    return plan, verdicts


def test_failed_interop_is_recorded_and_left_out(tmp_path):
    plan, verdicts = files(tmp_path, '"aaaaaaaaaaaa": {interop: passed, check: same_output}\n'
                                     '"bbbbbbbbbbbb": {interop: interop_failed, check: same_output, reason: "outputs_differ: x"}\n')
    document, measured = scope_results.merge(plan, verdicts)
    statuses = {s["id"]: s["status"] for s in yaml.safe_load(plan.read_text())["scopes"]}
    assert statuses == {"aaaaaaaaaaaa": "measured", "bbbbbbbbbbbb": "interop_failed", "cccccccccccc": "not_compilable"}
    assert [r["id"] for r in measured] == ["aaaaaaaaaaaa"]
    effective = tmp_path / "effective.yaml"
    effective.write_text("run: {harness: {iterations: 5}}\n")
    prepared = yaml.safe_load(scope_results.prepared(document, measured, effective, tmp_path / "prepared.yaml").read_text())
    assert [c["id"] for c in prepared["cases"]] == ["scope:aaaaaaaaaaaa:before", "scope:aaaaaaaaaaaa:after"]
    assert prepared["cases"][1] == {"id": "scope:aaaaaaaaaaaa:after", "type": "Scope", "algorithm": "f", "provider": "fixture",
                                 "operation": "after", "key": {"kind": "none"}, "harness": {"iterations": 5}, "inputSize": 64}


def test_a_compiled_scope_without_a_verdict_fails(tmp_path):
    plan, verdicts = files(tmp_path, '"aaaaaaaaaaaa": {interop: unchecked, check: none, reason: "no_output: x"}\n')
    with pytest.raises(scope_results.ScopeResultError, match="missing_verdict: scope bbbbbbbbbbbb"):
        scope_results.merge(plan, verdicts)


def test_an_identity_only_output_is_not_measured_and_a_randomized_one_is_unchecked(tmp_path):
    plan, verdicts = files(tmp_path, '"aaaaaaaaaaaa": {interop: not_comparable, check: same_output, reason: "identity_only_output: X"}\n'
                                     '"bbbbbbbbbbbb": {interop: unchecked, check: same_output, reason: "nondeterministic_output: y"}\n')
    _, measured = scope_results.merge(plan, verdicts)
    scopes = {s["id"]: s for s in yaml.safe_load(plan.read_text())["scopes"]}
    assert scopes["aaaaaaaaaaaa"]["status"] == "not_comparable"
    assert (scopes["bbbbbbbbbbbb"]["status"], scopes["bbbbbbbbbbbb"]["interop"]["result"]) == ("measured", "unchecked")
    assert [r["id"] for r in measured] == ["bbbbbbbbbbbb"]
