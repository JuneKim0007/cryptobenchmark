import json
import shutil

import pytest
from dataclasses import replace
from pathlib import Path

from helpers import ANY_EVIDENCE, TIMING, QUIET, row, summary
from test_stages import run  # noqa: F401  the recorded run, grouped

from perfrepair.catalog.screening import SCREENING, PlatformRule
from perfrepair.dto.lifecycle import Lifecycle
from perfrepair.dto.perf_mode import PerfMode
from perfrepair.catalog.bundled_providers import BundledCatalog, BundledRow
from perfrepair.dto.screen import Verdict
from perfrepair.result.provider_path import SiteProviders, site_providers
from perfrepair.dto.dossier import Dossier
from perfrepair.dto.site import Scope, scope_id
from perfrepair.repair.dossier import dossier
from perfrepair.dto.dossier import PROVIDER_HELD_KEY
from perfrepair.dto.unit import Link, Unit, unit_id
from perfrepair.result.dossier import build_dossiers
from perfrepair.result.unit_dossiers import by_unit
from perfrepair.validation.dossier_units import validate_dossier_units
from perfrepair.screen.catalog import load_catalog
from perfrepair.validation.dossiers import validate_dossiers
from perfrepair.check.run import validate_run
from perfrepair.screen.catalog import screening_catalog

F = Path(__file__).parent / "fixtures"
DEMO = F / "app_results" / "demo"
PARAMS = {"mode": "GCM", "tagBits": 128, "ivBytes": 12}
GROUPS = {"groups": [{"id": "g", "members": [1, 2, 3, 4]}, {"id": "lone", "members": [5]}],
          "items": {"1": {"qualified": "TypeA|ALG-A|P1", "group": "g", "runs": True},
                    "2": {"qualified": "TypeA|ALG-A|P2", "group": "g", "runs": True},
                    "3": {"qualified": "TypeA|alg-a-alias|P3", "group": "g", "runs": True},
                    "4": {"qualified": "TypeA|ALG-A|P4", "group": "g", "runs": False},
                    "5": {"qualified": "TypeA|ALG-L|P1", "group": "lone", "runs": True}},
          "interop": {"status": "checked", "pairs": [
              {"id": 1, "group": "g", "a": "TypeA|ALG-A|P1", "b": "TypeA|ALG-A|P2", "result": "pass", "reason": ""},
              {"id": 2, "group": "g", "a": "TypeA|ALG-A|P1", "b": "TypeA|alg-a-alias|P3", "result": "not_checkable",
               "reason": "no shared key size"}]}}
ROWS = [replace(row("c64", "P1", input_size=64), parameters=PARAMS),
        replace(row("c4k", "P1", input_size=4096), parameters=PARAMS),
        replace(row("o64", "P2", input_size=64), parameters={**PARAMS, "ivBytes": 16}),
        replace(row("o4k", "P2", input_size=4096), parameters={**PARAMS, "ivBytes": 16}),
        replace(row("a64", "P3", algorithm="alg-a-alias", input_size=64), parameters=PARAMS)]
M = {"c64": {"timeNs": summary(100), "allocationCount": summary(10)}, "c4k": {"timeNs": summary(900), "allocationCount": None},
     "o64": {"timeNs": summary(80), "allocationCount": summary(12)}, "o4k": {"timeNs": summary(950), "allocationCount": None},
     "a64": {"timeNs": summary(99, spread=30.0), "allocationCount": None}}


def scope(provider="P1", algorithm="ALG-A", resolution="explicit", input_size=100, key_size=128, line=2):
    return Scope(scope_id("app", "A.java", "f", line, "TypeA.getInstance"), "app", "A.java", line, "TypeA.getInstance",
                 "f", 1, 3, "TypeA", algorithm, provider, resolution, key_size, input_size)


def build(scopes, tmp_path, app_doc=None, rows=ROWS, measurements=M, groups=GROUPS, verdicts=None, perf=None):
    perf = perf or (TIMING if rows else ANY_EVIDENCE)
    (tmp_path / "A.java").write_text("void f() {\n  TypeA.getInstance(\"ALG-A\", \"P1\");\n}\nvoid g() {}\n")
    return build_dossiers("app", scopes, app_doc or {"bundled": []}, groups, rows, measurements, tmp_path, verdicts, perf)


def failing(*results):
    pairs = [{**p, "result": r, "reason": r} for p, r in zip(GROUPS["interop"]["pairs"], results)]
    return {**GROUPS, "interop": {"status": "checked", "pairs": pairs}}


def test_options_are_the_runnable_other_members_with_estimates_at_the_nearest_size(tmp_path):
    doc = build([scope()], tmp_path, perf=ANY_EVIDENCE)
    [d] = [Dossier.from_json(x) for x in doc["dossiers"]]
    assert d.current == "TypeA|ALG-A|P1" and d.source == "void f() {\n  TypeA.getInstance(\"ALG-A\", \"P1\");\n}"
    assert [(o.alias, o.item) for o in d.options] == [("R1", "TypeA|ALG-A|P2"), ("R2", "TypeA|alg-a-alias|P3")]
    r1 = d.options[0]
    assert r1.pins == {"ivBytes": 16}
    time = next(e for e in r1.estimates if e.metric == "timeNs")
    assert (time.ratio, time.configuration, time.n) == (0.8, "OP1 key 128 input 64 WARM", 50) and time.pImprove > 0.99
    alloc = next(e for e in r1.estimates if e.metric == "allocationCount")
    assert alloc.ratio == 1.2 and alloc.pImprove < 0.01


def test_a_same_parameter_option_has_nothing_to_pin(tmp_path):
    raw = build([scope()], tmp_path)["dossiers"][0]["options"][1]
    assert raw["item"] == "TypeA|alg-a-alias|P3" and raw["pins"] == {}
    assert [e["metric"] for e in raw["estimates"]] == ["timeNs"]


def test_a_row_without_parameters_is_a_coded_error(tmp_path):
    with pytest.raises(ValueError, match="missing_parameters: rows a64"):
        build([scope()], tmp_path, rows=ROWS[:4] + [row("a64", "P3", algorithm="alg-a-alias", input_size=64)])


def test_no_shared_configuration_gives_unknown_pins_that_survive_the_round_trip(tmp_path):
    s = scope(key_size=256)
    doc = build([s], tmp_path, perf=ANY_EVIDENCE)
    assert [o["pins"] for o in doc["dossiers"][0]["options"]] == [None, None]
    d = Dossier.from_json(json.loads(json.dumps(doc["dossiers"][0])))
    assert [o.pins for o in d.options] == [None, None] and d.to_json() == doc["dossiers"][0]
    assert validate_dossiers(doc, [s], GROUPS, None) == []


def test_a_one_run_estimate_has_no_pimprove_and_validates(tmp_path):
    one = {**M, "c64": {"timeNs": summary(100, n=1), "allocationCount": None}}
    doc = build([scope()], tmp_path, measurements=one)
    e = doc["dossiers"][0]["options"][0]["estimates"][0]
    assert (e["metric"], e["n"], e["pImprove"]) == ("timeNs", 1, None)
    assert validate_dossiers(doc, [scope()], GROUPS, None) == []


def test_a_pins_value_that_is_neither_an_object_nor_null_is_caught(tmp_path):
    doc = build([scope()], tmp_path)
    doc["dossiers"][0]["options"][0]["pins"] = "ivBytes=16"
    assert any("neither an object nor null" in p for p in validate_dossiers(doc, [scope()], GROUPS, None))


def test_scopes_without_options_say_why(tmp_path):
    scopes = [scope(provider=None, resolution="unresolved_provider"), scope(provider="P9", line=1),
              scope(algorithm="ALG-L", line=3), scope(provider="Elsewhere", line=5, resolution="not_on_device")]
    doc = build(scopes, tmp_path)
    assert doc["dossiers"] == [] and doc["noOptions"] == [
        {"scope": scopes[0].id, "reason": "unresolved"}, {"scope": scopes[1].id, "reason": "not_grouped"},
        {"scope": scopes[2].id, "reason": "no_alternative"}, {"scope": scopes[3].id, "reason": "not_on_device"}]
    assert validate_dossiers(doc, scopes, GROUPS, None) == []


def test_only_the_selected_metrics_are_estimated_and_an_option_without_one_is_dropped(tmp_path):
    perf = PerfMode.parse(["memAlloc"])
    gaining = {**M, "o64": {"timeNs": summary(80), "allocationCount": summary(8)}}
    doc = build([scope()], tmp_path, perf=perf, measurements=gaining)
    [d] = doc["dossiers"]
    assert doc["perfMode"] == ["memAlloc"]
    assert [(o["alias"], o["item"]) for o in d["options"]] == [("R1", "TypeA|ALG-A|P2")]
    assert [e["metric"] for e in d["options"][0]["estimates"]] == ["allocationCount"]
    assert validate_dossiers(doc, [scope()], GROUPS, None) == []
    d["options"][0]["estimates"].append({**d["options"][0]["estimates"][0], "metric": "timeNs"})
    assert any("not one of the perfMode's" in p for p in validate_dossiers(doc, [scope()], GROUPS, None))


def test_a_selected_metric_no_option_has_is_a_static_no_evidence_never_a_proxy(tmp_path):
    doc = build([scope()], tmp_path, perf=PerfMode.parse(["energy", "latency"]))
    assert doc["dossiers"] == [] and doc["noOptions"] == [{"scope": scope().id, "reason": "no_evidence: energyJ"}]
    assert validate_dossiers(doc, [scope()], GROUPS, None) == []


def test_the_builder_is_deterministic_and_validates(tmp_path):
    first, second = build([scope()], tmp_path), build([scope()], tmp_path)
    assert json.dumps(first) == json.dumps(second)
    assert set(first) == {"schemaVersion", "app", "perfMode", "maxChange", "dossiers", "noOptions", "notOffered", "units"}
    assert validate_dossiers(first, [scope()], GROUPS, None) == []


def test_the_validator_catches_a_foreign_option_and_a_missing_scope(tmp_path):
    doc = build([scope()], tmp_path)
    doc["dossiers"][0]["options"][0]["item"] = "TypeA|ALG-L|P1"
    other = scope(line=3)
    problems = validate_dossiers(doc, [scope(), other], GROUPS, None)
    assert any("not another member" in p for p in problems)
    assert any(f"{other.id}: neither a dossier nor in noOptions" in p for p in problems)


def test_each_option_carries_its_pairs_interop_status(tmp_path):
    doc = build([scope()], tmp_path)
    assert [o["interop"] for o in doc["dossiers"][0]["options"]] == ["pass", "not_checkable"]
    unplanned = {**GROUPS, "interop": {"status": "checked", "pairs": GROUPS["interop"]["pairs"][:1]}}
    assert [o["interop"] for o in build([scope()], tmp_path, groups=unplanned)["dossiers"][0]["options"]] == [
        "pass", "not_planned"]


def test_a_failed_pair_is_never_an_option(tmp_path):
    doc = build([scope()], tmp_path, groups=failing("fail", "pass"))
    assert [(o["alias"], o["item"], o["interop"]) for o in doc["dossiers"][0]["options"]] == [
        ("R1", "TypeA|alg-a-alias|P3", "pass")]
    assert validate_dossiers(doc, [scope()], failing("fail", "pass"), None) == []


def test_a_scope_whose_every_option_failed_interop_has_no_options(tmp_path):
    doc = build([scope()], tmp_path, groups=failing("fail", "fail"))
    assert doc["dossiers"] == [] and doc["noOptions"] == [{"scope": scope().id, "reason": "interop_failed"}]
    assert validate_dossiers(doc, [scope()], failing("fail", "fail"), None) == []


def test_groups_without_an_interop_section_are_refused(tmp_path):
    bare = {k: v for k, v in GROUPS.items() if k != "interop"}
    with pytest.raises(ValueError, match="no interop section"):
        build([scope()], tmp_path, groups=bare)
    assert validate_dossiers(build([scope()], tmp_path), [scope()], bare, None) == [
        "groups.json has no interop section; rerun grouping report"]


@pytest.mark.parametrize("status, problem", [
    ("maybe", "interop 'maybe' is not one of"),
    ("fail", "interop fail; a failed pair is never an option"),
    ("not_run", "interop not_run is not the groups.json status pass"),
])
def test_the_validator_checks_each_options_interop(tmp_path, status, problem):
    doc = build([scope()], tmp_path)
    doc["dossiers"][0]["options"][0]["interop"] = status
    assert any(problem in p for p in validate_dossiers(doc, [scope()], GROUPS, None))


def test_an_option_without_interop_does_not_parse(tmp_path):
    doc = build([scope()], tmp_path)
    del doc["dossiers"][0]["options"][0]["interop"]
    assert any("does not parse into Dossier" in p for p in validate_dossiers(doc, [scope()], GROUPS, None))


def test_a_scopes_json_of_another_schema_is_refused_never_read_with_defaults(run):  # noqa: F811
    app = run / "demo"
    app.mkdir(parents=True)
    for name in ("scopes.json", "app.json", "units.json"):
        shutil.copy(DEMO / name, app / name)
    (app / "scopes.json").write_text((app / "scopes.json").read_text().replace('"schemaVersion": 5', '"schemaVersion": 4'))
    with pytest.raises(ValueError, match=r"^schema_version: .*scopes.json schemaVersion 4 is not 5; rerun"):
        dossier(run, "demo", F / "app", load_catalog(SCREENING), TIMING, **QUIET)


def test_the_command_writes_dossiers_from_a_recorded_run(run):  # noqa: F811
    app = run / "demo"
    app.mkdir(parents=True)
    for name in ("scopes.json", "app.json", "units.json"):
        shutil.copy(DEMO / name, app / name)
    doc = dossier(run, "demo", F / "app", load_catalog(SCREENING), TIMING, **QUIET)
    [d] = doc["dossiers"]
    assert d["current"] == "Cipher|AES/GCM/NoPadding|Slow" and d["source"].startswith("    byte[] seal(")
    [option] = d["options"]
    time = next(e for e in option["estimates"] if e["metric"] == "timeNs")
    assert option["item"] == "Cipher|AES/GCM/NoPadding|Fast" and time["ratio"] < 0.4 and time["pImprove"] == 1.0
    assert {n["reason"] for n in doc["noOptions"]} == {"unresolved", "no_alternative"}
    assert validate_run(run, screening_catalog(None))["demo/dossiers.json"] == []


def test_an_unknown_key_size_takes_every_measured_key_size_so_pins_are_known(tmp_path):
    doc = build([scope(key_size=None)], tmp_path)
    assert [o["pins"] for o in doc["dossiers"][0]["options"]] == [{"ivBytes": 16}, {}]


def _verdicts(**by_provider):
    """P1..P5 accepted under their own names unless a (status, canonical) is given."""
    names = {"P1": "ALG-A", "P2": "ALG-A", "P3": "ALG-A", "P4": "ALG-A", "P5": "ALG-L"}
    out = {}
    for v in GROUPS["items"].values():
        provider = v["qualified"].split("|")[2]
        status, canonical = by_provider.get(provider, ("accepted", names[provider]))
        out[v["qualified"]] = Verdict(status, "r", "S", canonical)
    return out


def test_a_deprecated_target_of_the_current_algorithm_is_an_option(tmp_path):
    verdicts = _verdicts(P1=("broken", "ALG-A"), P2=("broken", "ALG-A"), P3=("broken", "ALG-A"))
    doc = build([scope()], tmp_path, verdicts=verdicts)
    assert [(o["item"], o["screen"]) for o in doc["dossiers"][0]["options"]] == [
        ("TypeA|ALG-A|P2", "broken"), ("TypeA|alg-a-alias|P3", "broken")]
    assert validate_dossiers(doc, [scope()], GROUPS, verdicts) == []


@pytest.mark.parametrize("target", [("broken", "ALG-X"), ("platform_deprecated", "ALG-A")])
def test_a_target_that_lowers_the_status_is_never_an_option(tmp_path, target):
    verdicts = _verdicts(P2=target)
    doc = build([scope()], tmp_path, verdicts=verdicts)
    assert [(o["item"], o["screen"]) for o in doc["dossiers"][0]["options"]] == [("TypeA|alg-a-alias|P3", "accepted")]
    assert validate_dossiers(doc, [scope()], GROUPS, verdicts) == []


def test_a_scope_left_only_deprecated_targets_says_deprecated_only_before_interop(tmp_path):
    verdicts = _verdicts(P2=("broken", "ALG-X"), P3=("broken", "ALG-Y"))
    doc = build([scope()], tmp_path, groups=failing("fail", "fail"), verdicts=verdicts)
    assert doc["dossiers"] == [] and doc["noOptions"] == [{"scope": scope().id, "reason": "deprecated_only"}]
    assert validate_dossiers(doc, [scope()], failing("fail", "fail"), verdicts) == []
    idle = {**GROUPS, "items": {k: {**v, "runs": k == "1"} for k, v in GROUPS["items"].items()}}
    assert build([scope()], tmp_path, groups=idle, verdicts=verdicts)["noOptions"] == [
        {"scope": scope().id, "reason": "none_available"}]


def test_the_validator_refuses_an_option_that_lowers_the_status(tmp_path):
    doc = build([scope()], tmp_path, verdicts=_verdicts())
    problems = validate_dossiers(doc, [scope()], GROUPS, _verdicts(P2=("broken", "ALG-X")))
    assert any("R1: screen 'accepted' is not this app's status 'broken'" in p for p in problems)
    assert any("R1: TypeA|ALG-A|P2 is broken and lowers the status of TypeA|ALG-A|P1" in p for p in problems)
    assert any("without screen.json" in p for p in validate_dossiers(doc, [scope()], GROUPS, None))


MIXED = {"groups": [{"id": "g", "members": [1, 2]}],
         "items": {"1": {"qualified": "MessageDigest|SHA-512|P", "group": "g", "runs": True},
                   "2": {"qualified": "MessageDigest|SHA-256|BC", "group": "g", "runs": True}},
         "interop": {"status": "not_run", "pairs": []}}
MIXED_SCREEN = {1: Verdict("accepted", "r", "S", "SHA-512"), 2: Verdict("accepted", "r", "S", "SHA-256")}


@pytest.mark.parametrize("target_sdk, options, reasons", [(27, [("MessageDigest|SHA-256|BC", "accepted")], []),
                                                          (28, [], ["deprecated_only"]),
                                                          (34, [], ["deprecated_only"])])
def test_a_platform_deprecated_target_depends_on_the_apps_target_sdk(tmp_path, target_sdk, options, reasons):
    s = replace(scope(provider="P", algorithm="SHA-512"), engineType="MessageDigest")
    verdicts = load_catalog(SCREENING).handler().app_verdicts(MIXED, MIXED_SCREEN, target_sdk)
    doc = build([s], tmp_path, groups=MIXED, rows=[], verdicts=verdicts)
    assert [(o["item"], o["screen"]) for d in doc["dossiers"] for o in d["options"]] == options
    assert [n["reason"] for n in doc["noOptions"]] == reasons
    assert validate_dossiers(doc, [s], MIXED, verdicts) == []


def test_the_command_applies_the_apps_target_sdk_through_the_handler_it_is_given(run):  # noqa: F811
    app = run / "demo"
    app.mkdir(parents=True)
    shutil.copy(DEMO / "scopes.json", app / "scopes.json")
    shutil.copy(DEMO / "units.json", app / "units.json")
    packaged = load_catalog(SCREENING)
    rule = PlatformRule(28, None, "test rule", "S")
    handler = replace(packaged, screening=replace(packaged.screening,
                                                  platform={("Fast", "Cipher", "AES/GCM/NOPADDING"): rule}))
    facts = json.loads((DEMO / "app.json").read_text())
    for target_sdk, extra in ((27, set()), (28, {"deprecated_only"})):
        (app / "app.json").write_text(json.dumps({**facts, "targetSdk": target_sdk}))
        doc = dossier(run, "demo", F / "app", handler, TIMING, **QUIET)
        assert {n["reason"] for n in doc["noOptions"]} == {"unresolved", "no_alternative"} | extra
        assert len(doc["dossiers"]) == (0 if extra else 1)


def test_a_lifecycle_with_no_real_use_is_a_static_no_option_never_a_dossier(tmp_path):
    unused = replace(scope(), lifecycle=Lifecycle("no_real_use", binding="discarded"))
    doc = build([unused], tmp_path)
    assert doc["dossiers"] == [] and doc["noOptions"] == [{"scope": unused.id, "reason": "no_real_use"}]
    assert validate_dossiers(doc, [unused], GROUPS, None) == []
    wrong = {**doc, "noOptions": [{"scope": unused.id, "reason": "no_alternative"}]}
    assert any("no_real_use" in p for p in validate_dossiers(wrong, [unused], GROUPS, None))


def test_estimates_cover_only_the_operations_the_lifecycle_performs_and_pins_stay(tmp_path):
    rows = ROWS[:4] + [replace(row("c2", "P1", input_size=64, operation="OP2"), parameters=PARAMS),
                       replace(row("o2", "P2", input_size=64, operation="OP2"), parameters={**PARAMS, "ivBytes": 16})]
    m = {**M, "c2": {"timeNs": summary(100), "allocationCount": None}, "o2": {"timeNs": summary(50), "allocationCount": None}}
    only = replace(scope(), lifecycle=Lifecycle("bounded", binding="local", operations=("OP2",)))
    r1 = Dossier.from_json(build([only], tmp_path, rows=rows, measurements=m)["dossiers"][0]).options[0]
    assert {e.configuration for e in r1.estimates} == {"OP2 key 128 input 64 WARM"} and r1.pins == {"ivBytes": 16}
    unknown = replace(scope(), lifecycle=Lifecycle("bounded", binding="local"))
    r1 = Dossier.from_json(build([unknown], tmp_path, rows=rows, measurements=m)["dossiers"][0]).options[0]
    assert {e.configuration for e in r1.estimates} == {"OP1 key 128 input 64 WARM", "OP2 key 128 input 64 WARM"}


def _unit(*ids, kind="shared_key"):
    return Unit(unit_id("app", list(ids)), tuple(ids), tuple(
        Link(kind, a, b, (1,), (1,), "field" if kind == "shared_key" else "key") for a, b in zip(ids, ids[1:])))


def _with_and_without():
    return [scope(), scope(line=30, algorithm="ALG-NONE")]


def test_a_member_without_options_stays_and_the_others_are_still_asked(tmp_path):
    has, lacks = _with_and_without()
    plain = build([has, lacks], tmp_path)
    own = plain["noOptions"][0]["reason"]
    unit = _unit(has.id, lacks.id)
    doc = by_unit(plain, [unit], [has, lacks], GROUPS)
    assert [d["scope"]["id"] for d in doc["dossiers"]] == [has.id] and doc["noOptions"] == plain["noOptions"]
    assert doc["units"] == [unit.to_json() | {"stays": [{"scope": lacks.id, "current": "TypeA|ALG-NONE|P1", "reason": own}],
                                              "pairs": []}]
    assert validate_dossier_units(doc, [unit], [has, lacks], GROUPS) == []
    assert validate_dossiers(doc, [has, lacks], GROUPS, None) == []


def test_an_inverse_link_carries_the_interop_of_every_two_items_a_replace_can_leave_its_sides_on(tmp_path):
    has, lacks = _with_and_without()
    unit = _unit(has.id, lacks.id, kind="inverse")
    [entry] = by_unit(build([has, lacks], tmp_path), [unit], [has, lacks], GROUPS)["units"]
    assert entry["pairs"] == [{"a": "TypeA|ALG-A|P2", "b": "TypeA|ALG-NONE|P1", "status": "not_planned"},
                              {"a": "TypeA|ALG-NONE|P1", "b": "TypeA|alg-a-alias|P3", "status": "not_planned"}]
    same = scope(line=40)
    [entry] = by_unit(build([has, same], tmp_path), [_unit(has.id, same.id, kind="inverse")], [has, same], GROUPS)["units"]
    assert entry["pairs"] == [{"a": "TypeA|ALG-A|P2", "b": "TypeA|alg-a-alias|P3", "status": "not_planned"}]


def _held_contract():
    return {**GROUPS, "items": {**GROUPS["items"], "5": {**GROUPS["items"]["5"], "keyContract": "provider_held"}}}


def test_a_provider_held_key_on_any_member_keeps_every_member(tmp_path):
    has, lone = scope(), scope(line=30, algorithm="ALG-L")
    groups, unit = _held_contract(), _unit(has.id, lone.id)
    doc = by_unit(build([has, lone], tmp_path, groups=groups), [unit], [has, lone], groups)
    assert doc["dossiers"] == [] and doc["units"] == []
    assert {n["scope"]: n["reason"] for n in doc["noOptions"]} == {has.id: PROVIDER_HELD_KEY, lone.id: "no_alternative"}
    assert validate_dossier_units(doc, [unit], [has, lone], groups) == []


def test_a_keystore_key_source_alone_is_a_declared_risk_not_a_keep(tmp_path):
    has, lacks = _with_and_without()
    stored = replace(lacks, keySource="keystore")
    doc = by_unit(build([has, stored], tmp_path), [_unit(has.id, stored.id)], [has, stored], GROUPS)
    assert [d["scope"]["id"] for d in doc["dossiers"]] == [has.id]


def test_every_unit_with_a_member_with_options_is_asked(tmp_path):
    has, lacks = _with_and_without()
    units = [_unit(has.id), _unit(lacks.id)]
    doc = by_unit(build([has, lacks], tmp_path), units, [has, lacks], GROUPS)
    assert doc["units"] == [units[0].to_json() | {"stays": [], "pairs": []}]
    assert [d["scope"]["id"] for d in doc["dossiers"]] == [has.id]
    assert validate_dossier_units(doc, units, [has, lacks], GROUPS) == []


def test_the_unit_validator_refuses_a_wrong_key_contract_keep_and_lost_units(tmp_path):
    has, lacks = _with_and_without()
    unit = _unit(has.id, lacks.id)
    plain = build([has, lacks], tmp_path)
    held = {**plain, "dossiers": [], "noOptions": plain["noOptions"] + [{"scope": has.id, "reason": PROVIDER_HELD_KEY}]}
    assert any("no member's key is provider-held" in p for p in validate_dossier_units(held, [unit], [has, lacks], GROUPS))
    lone = scope(line=30, algorithm="ALG-L")
    both = build([has, lone], tmp_path)
    assert any("has a dossier although" in p
               for p in validate_dossier_units(both, [_unit(has.id, lone.id)], [has, lone], _held_contract()))
    lost = {**by_unit(plain, [unit], [has, lacks], GROUPS), "units": []}
    assert any("units are not the units.json" in p for p in validate_dossier_units(lost, [unit], [has, lacks], GROUPS))



def test_another_spelling_of_the_current_engine_is_not_offered_and_says_same_engine(tmp_path):
    groups = {**GROUPS, "items": {**GROUPS["items"], "2": {"qualified": "TypeA|ALG_128-A|P1", "group": "g", "runs": True}}}
    verdicts = {v["qualified"]: Verdict("accepted", "r", canonical="ALG-A") for v in groups["items"].values()}
    doc = build([scope()], tmp_path, groups=groups, verdicts=verdicts, rows=[r for r in ROWS if r.provider != "P2"])
    assert [o["item"] for d in doc["dossiers"] for o in d["options"]] == ["TypeA|alg-a-alias|P3"]
    assert [(n["item"], n["reasons"]) for n in doc["notOffered"]] == [("TypeA|ALG_128-A|P1", ["same_engine"])]
    assert validate_dossiers(doc, [scope()], groups, verdicts) == []


def test_a_member_from_another_provider_of_the_same_name_is_the_provider_path_and_by_order_says_so(tmp_path):
    verdicts = {v["qualified"]: Verdict("accepted", "r", canonical=v["qualified"].split("|")[1].upper())
                for v in GROUPS["items"].values()}
    doc = build([scope(resolution="default")], tmp_path, verdicts=verdicts)
    tracks = {o["item"]: (o["track"], o["needsReview"]) for o in doc["dossiers"][0]["options"]}
    assert tracks["TypeA|ALG-A|P2"] == ("provider_path", ["resolved_by_order"])
    assert tracks["TypeA|alg-a-alias|P3"][0] == "recommendation"
    named = build([scope()], tmp_path, verdicts=verdicts)["dossiers"][0]["options"][0]
    assert (named["track"], named["needsReview"]) == ("provider_path", [])


def test_a_shipped_provider_the_app_inserts_first_is_what_a_default_site_is_on_and_the_platform_its_path(tmp_path):
    providers = site_providers({"P2": "g:lib"}, {"bundled": [{"artifact": "g:lib", "providerName": "Lib"}],
                                                 "registers": [{"file": "A.kt", "line": 1, "expr": "Lib.make()",
                                                                "call": "insertProviderAt", "position": "1"}]},
                               BundledCatalog({"g:lib": BundledRow("g:lib", "Lib", "x.Lib#make", "S", alias="P2")}))
    assert providers == SiteProviders({"Lib": "P2"}, "P2")
    s, faster = scope(resolution="default"), {**M, "c64": M["o64"], "o64": M["c64"]}
    doc = build_dossiers("app", [s], {"bundled": []}, GROUPS, ROWS, faster, _source(tmp_path), None, TIMING, None,
                         {"P1", "P2", "P3"}, providers)
    d = doc["dossiers"][0]
    assert d["current"] == "TypeA|ALG-A|P2" and "TypeA|ALG-A|P1" in [o["item"] for o in d["options"]]
    assert all("resolved_by_order" in o["needsReview"] for o in d["options"])
    named = replace(s, provider="Lib", resolution="not_on_device")
    doc = build_dossiers("app", [named], {"bundled": []}, GROUPS, ROWS, faster, tmp_path, None, TIMING, None,
                         {"P1", "P2", "P3"}, SiteProviders({"Lib": "P2"}))
    assert doc["dossiers"][0]["current"] == "TypeA|ALG-A|P2"
    assert all("resolved_by_order" not in o["needsReview"] for o in doc["dossiers"][0]["options"])


def test_an_added_provider_or_one_at_another_position_moves_no_default_site():
    catalog = BundledCatalog({"g:lib": BundledRow("g:lib", "Lib", "x.Lib", "S", alias="P2")})
    for call, position in (("addProvider", None), ("insertProviderAt", "3")):
        app = {"bundled": [{"artifact": "g:lib", "providerName": "Lib"}],
               "registers": [{"file": "A.kt", "line": 1, "expr": "new Lib()", "call": call, "position": position}]}
        assert site_providers({"P2": "g:lib"}, app, catalog).first is None


def _source(tmp_path):
    (tmp_path / "A.java").write_text("void f() {\n  TypeA.getInstance(\"ALG-A\", \"P1\");\n}\nvoid g() {}\n")
    return tmp_path
