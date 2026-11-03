"""Family candidates into a dossier: maxChange decides what is offered; the gate, the report and the validators agree."""
import json
from dataclasses import replace

import pytest
from helpers import TIMING, row, summary

from perfrepair.ai.suggest.site_replace.render import render
from perfrepair.catalog.types import Types
from perfrepair.data_handler.inbound.probe import Probe
from perfrepair.dto.change import PairDiff
from perfrepair.dto.perf_mode import PerfMode
from perfrepair.dto.site import Dossier, Estimate, Option, Scope, scope_id
from perfrepair.dto.types import Properties, Strength, TypeRow
from perfrepair.dto.unit import Link, Stay, Unit, UnitDossiers, unit_id
from perfrepair.report.recommendations import recommendations, summed
from perfrepair.result.candidates import Family
from perfrepair.result.dossier import available_providers, build_dossiers
from perfrepair.result.gain import no_gain
from perfrepair.validation.dossiers import check_dossier, validate_dossiers
from perfrepair.validation.report import _recommendations
from perfrepair.validation.suggest.site_replace import check_reply

A, B, C, D = "TypeA|WEAK|P1", "TypeA|STRONG|P1", "TypeA|LATE|P1", "TypeA|GONE|P1"
PARAMS = {"mode": "x"}


def type_row(name, bits, min_sdk=1, out=32) -> TypeRow:
    return TypeRow("fam", name, "digest", Properties(False, True, "none", "none", out, "none"), Strength(bits=bits), "S", min_sdk, "S")


TYPES = Types({("fam", n.upper()): type_row(n, b, s) for n, b, s in
               (("WEAK", 0, 1), ("STRONG", 128, 1), ("LATE", 256, 28), ("GONE", 128, 1))}, {}, frozenset({"digest"}), {"S": "x"})
GROUPS = {"groups": [], "interop": {"status": "checked", "pairs": []},
          "items": {str(n): {"qualified": q, "group": None, "runs": q != D} for n, q in enumerate((A, B, C, D), 1)}}
ROWS = [replace(row(f"r{n}", "P1", algorithm=name), parameters=PARAMS) for n, name in enumerate(("WEAK", "STRONG", "LATE"))]
M = {f"r{n}": {"timeNs": summary(100 - n), "allocationCount": None} for n in range(3)}


def scope(sinks=("return",)) -> Scope:
    return Scope(scope_id("app", "A.java", "f", 2, "TypeA.get"), "app", "A.java", 2, "TypeA.get", "f", 1, 3, "TypeA", "WEAK",
                 "P1", "explicit", None, None, sinks)


def family(top, min_sdk=21) -> Family:
    return Family({q: "fam" for q in (A, B, C, D)}, {A: "WEAK", B: "STRONG", C: "LATE", D: "GONE"}, TYPES, min_sdk, frozenset(), top)


def build(tmp_path, top, sinks=("return",)):
    (tmp_path / "A.java").write_text("void f() {\n  x();\n}\n")
    return build_dossiers("app", [scope(sinks)], {"bundled": []}, GROUPS, ROWS, M, tmp_path, None, TIMING, family(top))


def test_drop_in_offers_no_other_class_and_keeps_it_as_a_recommendation(tmp_path):
    doc = build(tmp_path, "drop-in")
    assert doc["dossiers"] == [] and doc["noOptions"][0]["reason"] == "not_grouped"
    assert [(n["item"], n["change"]) for n in doc["notOffered"] if n["change"] != "rejected"] == [(B, "local-edit")]


def test_local_edit_offers_the_candidate_with_its_class_and_diff(tmp_path):
    doc = build(tmp_path, "local-edit")
    option = doc["dossiers"][0]["options"][0]
    assert (option["item"], option["change"]) == (B, "local-edit")
    assert option["diff"] == {"input": "same", "key": "same", "output": "bytes", "reach": "return", "addsDependency": False}
    assert validate_dossiers(doc, [scope()], GROUPS, None) == []


def test_each_rejected_candidate_keeps_its_reason(tmp_path):
    reasons = {n["item"]: n["reasons"] for n in build(tmp_path, "local-edit")["notOffered"]}
    assert reasons == {C: ["unavailable"], D: ["not_measured"]}


def test_persisted_output_stays_a_recommendation_until_migration(tmp_path):
    assert build(tmp_path, "local-edit", ("persist",))["dossiers"] == []
    kept = build(tmp_path, "local-edit", ("persist",))["notOffered"]
    assert {n["item"]: n["change"] for n in kept}[B] == "migration"
    option = build(tmp_path, "migration", ("persist",))["dossiers"][0]["options"][0]
    assert (option["item"], option["change"], option["diff"]["reach"]) == (B, "migration", "persist")


def test_without_a_family_nothing_is_classed(tmp_path):
    (tmp_path / "A.java").write_text("void f() {\n  x();\n}\n")
    doc = build_dossiers("app", [scope()], {"bundled": []}, GROUPS, ROWS, M, tmp_path, None, TIMING)
    assert doc["notOffered"] == [] and doc["maxChange"] == "drop-in"


def test_a_drop_in_option_writes_no_change_so_its_dossier_is_unchanged():
    assert set(Option("R1", B, {}, "pass").to_json()) == {"alias", "item", "pins", "interop", "screen", "estimates"}


def test_the_validator_refuses_an_option_above_max_change(tmp_path):
    raw = build(tmp_path, "migration", ("persist",))["dossiers"][0]
    problems = check_dossier(raw, "app", TIMING, "local-edit")[1]
    assert any("above maxChange local-edit" in p for p in problems)


def test_the_validator_refuses_a_recommendation_within_max_change(tmp_path):
    doc = build(tmp_path, "local-edit", ("persist",))
    doc["maxChange"] = "migration"
    assert any("within maxChange" in p for p in validate_dossiers(doc, [scope(("persist",))], GROUPS, None))


def _reply(option="R1"):
    return json.dumps({"decision": "replace", "reason": "r", "deciding": ["timeNs"], "members": [{"member": "S1", "option": option, "risks": ["unverified_interop", "key_compatibility"],
                       "edits": [{"kind": "set_algorithm", "provider": "", "algorithm": "STRONG", "parameters": []}]}]})


def _unit(change="local-edit") -> UnitDossiers:
    d = Dossier(scope(("local",)), "src", A, (Option("R1", B, {}, "not_planned", (FASTER,), change=change, diff=PairDiff("same", "same", "bytes", "local")),))
    return UnitDossiers(Unit(unit_id("app", [d.key]), (d.key,)), (d,))


FASTER = Estimate("timeNs", 0.6, 0.99, 50, "OP key 1 input 1 p")


def test_gate_c_takes_a_pick_within_max_change():
    decision, problems = check_reply(_reply(), _unit(), "local-edit")
    assert problems == [] and decision["replacements"][0]["option"] == B


@pytest.mark.parametrize("change,top", [("local-edit", "drop-in"), ("migration", "local-edit")])
def test_gate_c_refuses_a_listed_pick_above_max_change(change, top):
    decision, problems = check_reply(_reply(), _unit(change), top)
    assert decision is None and any(f"above maxChange {top}" in p for p in problems)


def test_gate_c_refuses_a_pick_outside_the_list():
    decision, problems = check_reply(_reply("R9"), _unit(), "local-edit")
    assert decision is None and any("is not one of R1" in p for p in problems)


def test_the_report_recommends_above_max_change_and_counts_rejects(tmp_path):
    report = recommendations(build(tmp_path, "local-edit", ("persist",)))
    assert report["maxChange"] == "local-edit"
    assert [(n["item"], n["change"]) for n in report["recommendations"]] == [(B, "migration")]
    assert report["rejected"] == {"not_measured": 1, "unavailable": 1} and _recommendations(report) == []
    assert summed([report, report]) == {"recommendations": {"migration": 2}, "rejected": {"not_measured": 2, "unavailable": 2}}


def test_the_report_validator_refuses_a_recommendation_within_max_change():
    bad = {"maxChange": "migration", "recommendations": [{"scope": "s", "item": B, "change": "migration"}], "rejected": {}}
    assert _recommendations(bad)


def _pair(a_item, b_item):
    diff = PairDiff("same", "same", "bytes", "local")
    a = Dossier(replace(scope(("local",)), id="a"), "src", A, (Option("R1", B, {}, "not_planned", (FASTER,), change="local-edit", diff=diff),))
    b = Dossier(replace(scope(("local",)), id="b"), "src", A, (Option("R1", B, {}, "not_planned", (FASTER,), change="local-edit", diff=diff),))
    unit = UnitDossiers(Unit("u", ("a", "b"), (Link("inverse", "a", "b", (1,), (2,), "key"),)), (a, b))
    member = lambda m: {"member": m, "option": "R1", "risks": ["unverified_interop", "key_compatibility"],
                        "edits": [{"kind": "set_algorithm", "provider": "", "algorithm": "STRONG", "parameters": []}]}
    return unit, member


def test_inverse_sides_above_drop_in_must_end_on_one_item():
    unit, member = _pair(B, B)
    both = json.dumps({"decision": "replace", "reason": "r", "deciding": ["timeNs"], "members": [member("S1"), member("S2")]})
    assert check_reply(both, unit, "local-edit")[1] == []
    lone = UnitDossiers(replace(unit.unit), (unit.dossiers[0],), (Stay("b", A, "no_alternative"),))
    one = json.dumps({"decision": "replace", "reason": "r", "deciding": ["timeNs"], "members": [member("S1")]})
    assert any("must end both on one item" in p for p in check_reply(one, lone, "local-edit")[1])


def test_render_shows_the_class_and_diff_of_an_option_above_drop_in():
    text = render(_unit())
    assert "change: local-edit | input same | key same | output bytes | reach local" in text
    plain = Dossier(scope(), "src", A, (Option("R1", B, {}, "pass"),))
    assert "change:" not in render(UnitDossiers(Unit(unit_id("app", [plain.key]), (plain.key,)), (plain,)))


def test_a_candidate_of_the_same_name_is_left_to_grouping():
    f = Family({A: "fam", "TypeA|weak|P2": "fam"}, {A: "WEAK", "TypeA|weak|P2": "weak"}, TYPES, 21)
    assert f.items(A, set()) == []


H = "TypeA|WEAK|HARNESS"
GROUPED = {"groups": [{"id": "g", "family": "fam", "members": [1, 2]}], "interop": {"status": "checked", "pairs": []},
           "items": {"1": {"qualified": A, "group": "g", "runs": True}, "2": {"qualified": H, "group": "g", "runs": True}}}
H_ROWS = [replace(row("a", "P1", algorithm="WEAK"), parameters=PARAMS), replace(row("h", "HARNESS", algorithm="WEAK"), parameters=PARAMS)]
H_M = {"a": {"timeNs": summary(100)}, "h": {"timeNs": summary(80)}}


def _harness(tmp_path, top, available):
    (tmp_path / "A.java").write_text("void f() {\n  x();\n}\n")
    f = Family({A: "fam", H: "fam"}, {A: "WEAK", H: "WEAK"}, TYPES, 21, frozenset(), top)
    return build_dossiers("app", [scope(("local",))], {"bundled": []}, GROUPED, H_ROWS, H_M, tmp_path, None, TIMING, f, available)


def test_a_harness_only_provider_the_app_does_not_ship_is_no_drop_in(tmp_path):
    doc = _harness(tmp_path, "drop-in", {"P1"})
    assert doc["dossiers"] == [] and doc["noOptions"][0]["reason"] == "none_available"
    [kept] = doc["notOffered"]
    assert (kept["item"], kept["change"], kept["diff"]["addsDependency"]) == (H, "migration", True)


def test_under_migration_it_is_an_option_whose_diff_adds_a_dependency(tmp_path):
    doc = _harness(tmp_path, "migration", {"P1"})
    [option] = doc["dossiers"][0]["options"]
    assert (option["item"], option["change"], option["diff"]["addsDependency"], option["diff"]["output"]) == (H, "migration", True, "same")
    assert validate_dossiers(doc, [scope(("local",))], GROUPED, None) == []
    assert "adds a dependency" in render(UnitDossiers(Unit("u", (scope().id,)), (Dossier.from_json(doc["dossiers"][0]),)))


def test_a_provider_the_app_ships_stays_a_drop_in(tmp_path):
    [option] = _harness(tmp_path, "drop-in", {"P1", "HARNESS"})["dossiers"][0]["options"]
    assert option["item"] == H and "change" not in option


def test_available_is_the_platform_and_what_the_app_ships_also_under_the_harness_name():
    platform = frozenset({"P1"})
    harness = {"Ours": "org.example:lib", "Other": "org.example:other"}
    app = {"bundled": [{"artifact": "org.example:lib", "providerName": "Lib"}, {"artifact": "org.example:none", "providerName": None}]}
    assert available_providers(platform, harness, app) == {"P1", "Lib", "Ours"}
    assert available_providers(platform, harness, {}) == {"P1"}


def test_the_probe_names_a_harness_providers_artifact_without_its_version():
    probe = Probe({"providers": [{"name": "P1", "origin": "platform"}, {"name": "Ours", "origin": "bundled", "artifact": "org.example:lib:1.2"}]})
    assert probe.harness_artifacts() == {"Ours": "org.example:lib"}


def _estimate(ratio, p, metric="timeNs", n=9):
    return Estimate(metric, ratio, p, n, "OP key 1 input 1 p")


@pytest.mark.parametrize("estimates,want", [
    ((_estimate(20.0, 0.0),), True),
    ((_estimate(20.0, 0.0), _estimate(1.5, 0.01, "allocationCount")), True),
    ((_estimate(20.0, 0.0), _estimate(0.9, 0.99, "allocationCount")), False),
    ((_estimate(1.01, 0.0),), False),
    ((_estimate(20.0, 0.4),), False),
    ((_estimate(20.0, None, n=1),), False),
    ((), False)])
def test_no_gain_is_one_metric_proven_worse_and_none_better(estimates, want):
    assert no_gain(estimates) is want


def test_a_single_window_reading_does_not_save_a_proven_slower_option():
    assert no_gain((_estimate(1.5, 0.0), _estimate(1.56, None, n=1)))


def test_a_single_window_reading_that_improves_keeps_the_trade_off():
    assert not no_gain((_estimate(1.5, 0.0), _estimate(0.8, None, n=1)))


def test_an_unchanged_metric_does_not_save_a_proven_slower_option():
    assert no_gain((_estimate(1.5, 0.0), _estimate(1.0, 0.5)))


def _slow(tmp_path, top="drop-in"):
    (tmp_path / "A.java").write_text("void f() {\n  x();\n}\n")
    f = Family({A: "fam", H: "fam"}, {A: "WEAK", H: "WEAK"}, TYPES, 21, frozenset(), top)
    slow = {"a": {"timeNs": summary(100)}, "h": {"timeNs": summary(2000)}}
    return build_dossiers("app", [scope(("local",))], {"bundled": []}, GROUPED, H_ROWS, slow, tmp_path, None, TIMING, f, {"P1", "HARNESS"})


def test_a_twenty_times_slower_candidate_is_rejected_no_gain_and_the_scope_says_so(tmp_path):
    doc = _slow(tmp_path)
    assert doc["dossiers"] == [] and doc["noOptions"] == [{"scope": scope().id, "reason": "no_gain"}]
    assert [(n["item"], n["change"], n["reasons"]) for n in doc["notOffered"]] == [(H, "rejected", ["no_gain"])]
    assert validate_dossiers(doc, [scope(("local",))], GROUPED, None) == []


def test_the_validator_refuses_a_no_gain_option():
    d = Dossier(scope(), "src", A, (Option("R1", H, {}, "pass", (_estimate(20.0, 0.0),)),))
    assert any("no_gain" in p for p in check_dossier(d.to_json(), "app", TIMING)[1])
