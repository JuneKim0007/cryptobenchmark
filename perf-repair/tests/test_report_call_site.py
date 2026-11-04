"""Which kind each number is: the function when it has one, else the swapped call alone, each against the dossier's estimate."""
import yaml
from helpers import LATENCY, QUIET
from test_app_report import A, B, make_app, rows

from perfrepair.dto.report import CALL_SITE, FUNCTION
from perfrepair.files import read_json, read_yaml, write_json
from perfrepair.report.command import app_report
from perfrepair.result.category import at_call_site, truth
from perfrepair.run_dir import AppPaths
from perfrepair.validation.report import validate_report


def with_call_sites(tmp_path, scale=1.0):
    """A's and B's call measured from A's function cases; B's function was never compiled."""
    paths = make_app(tmp_path)
    plan = read_yaml(paths.scoped_plan)
    for record in plan["scopes"]:
        if record["id"] in (A, B):
            record["callSite"] = {"operation": "ENCRYPT", "variant": "notFixed", "status": "prepared"}
    paths.scoped_plan.write_text(yaml.safe_dump(plan))
    bench = read_json(paths.scoped_benchmark)
    cases = {c["id"]: c for c in bench["cases"]}
    for scope in (A, B):
        for side in ("before", "after"):
            case = {**cases[f"scope:{A}:{side}"], "id": f"scope:{scope}:callSite:{side}"}
            if side == "after":
                case = {**case, "metrics": {**case["metrics"], "timeNs": {**case["metrics"]["timeNs"], "runs": [v * scale for v in case["metrics"]["timeNs"]["runs"]]}}}
            bench["cases"].append(case)
    write_json(paths.scoped_benchmark, bench)
    return paths


def test_the_verdict_uses_the_function_when_present_else_the_call_and_says_so(tmp_path):
    with_call_sites(tmp_path)
    doc = app_report(tmp_path, "shop", LATENCY, **QUIET)
    a, b = rows(doc)[A], rows(doc)[B]
    assert validate_report(doc, "shop") == []
    assert a["measuredBy"] == FUNCTION and a["metrics"] == a["measurements"][FUNCTION]["metrics"]
    assert any(m["measured"] for m in a["measurements"][CALL_SITE]["metrics"])
    assert b["measuredBy"] == CALL_SITE and b["compile"]["status"] == "primitive_only"
    assert b["metrics"][0]["measured"] and b["verdict"] == b["measurements"][CALL_SITE]["verdict"]
    assert doc["funnel"]["measured"] == 1 and doc["funnel"]["measuredCallSite"] == 1
    text = AppPaths(tmp_path, "shop").report_md.read_text()
    assert "- measured by: callSite: the swapped call alone" in text and "- measured by: function: the function" in text


def test_an_unprepared_call_site_says_why_and_a_forged_kind_is_refused(tmp_path):
    paths = make_app(tmp_path)
    plan = read_yaml(paths.scoped_plan)
    for record in plan["scopes"]:
        record["callSite"] = {"operation": "ENCRYPT", "variant": "fixed", "status": "not_prepared", "reason": "not_prepared: no case"}
    paths.scoped_plan.write_text(yaml.safe_dump(plan))
    doc = app_report(tmp_path, "shop", LATENCY, **QUIET)
    b = rows(doc)[B]
    assert b["measuredBy"] is None
    assert b["measurements"][CALL_SITE]["metrics"][0]["reason"] == "call site not_prepared: not_prepared: no case"
    forged = {**doc, "scopes": [{**r, "measuredBy": CALL_SITE} for r in doc["scopes"]]}
    assert any("measuredBy" in p for p in validate_report(forged, "shop"))


def _measured(change):
    return [{"metric": "timeNs", "selected": True, "measured": True, "ratio": 1.0, "change": change}]


ESTIMATED_BETTER = [{"metric": "timeNs", "ratio": 0.7, "pImprove": 0.99, "configuration": "DIGEST key None input 64 WARM"}]


def test_the_call_alone_is_not_diluted_so_its_unchanged_contradicts_and_a_functions_never_does():
    assert truth(CALL_SITE, "notFixed", _measured("unchanged"), ESTIMATED_BETTER)["verdict"] == "contradicts"
    assert truth(FUNCTION, "notFixed", _measured("unchanged"), ESTIMATED_BETTER)["verdict"] == "agrees"


def test_a_fixed_scopes_function_is_its_setup_and_its_call_is_still_checked():
    assert truth(FUNCTION, "fixed", _measured("worse"), ESTIMATED_BETTER)["verdict"] == "not_applicable"
    assert truth(CALL_SITE, "fixed", _measured("worse"), ESTIMATED_BETTER)["mismatch"] == ["timeNs"]


def test_no_estimate_and_nothing_measured_are_named():
    assert truth(CALL_SITE, "notFixed", _measured("improved"), [])["verdict"] == "no_estimate"
    assert truth(CALL_SITE, "notFixed", [], ESTIMATED_BETTER)["verdict"] == "not_measured"


def test_a_call_is_compared_at_its_own_configuration_when_the_option_has_it():
    at = [{"metric": "timeNs", "ratio": r, "pImprove": 1.0, "configuration": c} for r, c in
          ((0.5, "DIGEST key None input 64 WARM"), (0.9, "DIGEST key None input 1024 WARM"), (1.2, "ENCRYPT key 256 input 64 WARM"))]
    assert [e["ratio"] for e in at_call_site(at, "DIGEST", {"inputSize": 1024, "keySize": None})] == [0.9]
    assert [e["ratio"] for e in at_call_site(at, "DIGEST", {"inputSize": 16384, "keySize": None})] == [0.5, 0.9]
    assert at_call_site(at, "SIGN", None) == at
