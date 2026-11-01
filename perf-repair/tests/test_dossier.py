import json
import shutil

import pytest
from dataclasses import replace
from pathlib import Path

from helpers import QUIET, row, summary
from test_stages import run  # noqa: F401  the recorded run, grouped

from perfrepair.dto.site import Dossier, Scope, scope_id
from perfrepair.repair.dossier import dossier
from perfrepair.result.dossier import build_dossiers
from perfrepair.validation.dossiers import validate_dossiers
from perfrepair.validation.run import validate_run

F = Path(__file__).parent / "fixtures"
DEMO = F / "apps" / "demo"
PARAMS = {"mode": "GCM", "tagBits": 128, "ivBytes": 12}
GROUPS = {"groups": [{"id": "g", "members": [1, 2, 3, 4]}, {"id": "lone", "members": [5]}],
          "items": {"1": {"qualified": "TypeA|ALG-A|P1", "group": "g", "runs": True},
                    "2": {"qualified": "TypeA|ALG-A|P2", "group": "g", "runs": True},
                    "3": {"qualified": "TypeA|alg-a-alias|P3", "group": "g", "runs": True},
                    "4": {"qualified": "TypeA|ALG-A|P4", "group": "g", "runs": False},
                    "5": {"qualified": "TypeA|ALG-L|P1", "group": "lone", "runs": True}}}
ROWS = [replace(row("c64", "P1", input_size=64), parameters=PARAMS),
        replace(row("c4k", "P1", input_size=4096), parameters=PARAMS),
        replace(row("o64", "P2", input_size=64), parameters={**PARAMS, "ivBytes": 16}),
        replace(row("o4k", "P2", input_size=4096), parameters={**PARAMS, "ivBytes": 16}),
        replace(row("a64", "P3", algorithm="alg-a-alias", input_size=64), parameters=PARAMS)]
M = {"c64": {"timeNs": summary(100), "allocations": summary(10)}, "c4k": {"timeNs": summary(900), "allocations": None},
     "o64": {"timeNs": summary(80), "allocations": summary(12)}, "o4k": {"timeNs": summary(950), "allocations": None},
     "a64": {"timeNs": summary(99, spread=30.0), "allocations": None}}


def scope(provider="P1", algorithm="ALG-A", resolution="explicit", input_size=100, key_size=128, line=2):
    return Scope(scope_id("app", "A.java", "f", line, "TypeA.getInstance"), "app", "A.java", line, "TypeA.getInstance",
                 "f", 1, 3, "TypeA", algorithm, provider, resolution, key_size, input_size)


def build(scopes, tmp_path, app_doc=None, rows=ROWS, measurements=M):
    (tmp_path / "A.java").write_text("void f() {\n  TypeA.getInstance(\"ALG-A\", \"P1\");\n}\nvoid g() {}\n")
    return build_dossiers("app", scopes, app_doc or {"bundled": []}, GROUPS, rows, measurements, tmp_path)


def test_options_are_the_runnable_other_members_with_estimates_at_the_nearest_size(tmp_path):
    doc = build([scope()], tmp_path)
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
    doc = build([s], tmp_path)
    assert [o["pins"] for o in doc["dossiers"][0]["options"]] == [None, None]
    d = Dossier.from_json(json.loads(json.dumps(doc["dossiers"][0])))
    assert [o.pins for o in d.options] == [None, None] and d.to_json() == doc["dossiers"][0]
    assert validate_dossiers(doc, [s], GROUPS) == []


def test_a_one_run_estimate_has_no_pimprove_and_validates(tmp_path):
    one = {**M, "c64": {"timeNs": summary(100, n=1), "allocations": None}}
    doc = build([scope()], tmp_path, measurements=one)
    e = doc["dossiers"][0]["options"][0]["estimates"][0]
    assert (e["metric"], e["n"], e["pImprove"]) == ("timeNs", 1, None)
    assert validate_dossiers(doc, [scope()], GROUPS) == []


def test_a_pins_value_that_is_neither_an_object_nor_null_is_caught(tmp_path):
    doc = build([scope()], tmp_path)
    doc["dossiers"][0]["options"][0]["pins"] = "ivBytes=16"
    assert any("neither an object nor null" in p for p in validate_dossiers(doc, [scope()], GROUPS))


def test_scopes_without_options_say_why(tmp_path):
    scopes = [scope(provider=None, resolution="unresolved_provider"), scope(provider="P9", line=1),
              scope(algorithm="ALG-L", line=3)]
    doc = build(scopes, tmp_path)
    assert doc["dossiers"] == [] and doc["noOptions"] == [
        {"scope": scopes[0].id, "reason": "unresolved"}, {"scope": scopes[1].id, "reason": "not_grouped"},
        {"scope": scopes[2].id, "reason": "no_alternative"}]
    assert validate_dossiers(doc, scopes, GROUPS) == []


def test_the_builder_is_deterministic_and_validates(tmp_path):
    first, second = build([scope()], tmp_path), build([scope()], tmp_path)
    assert json.dumps(first) == json.dumps(second)
    assert set(first) == {"schemaVersion", "app", "dossiers", "noOptions"}
    assert validate_dossiers(first, [scope()], GROUPS) == []


def test_the_validator_catches_a_foreign_option_and_a_missing_scope(tmp_path):
    doc = build([scope()], tmp_path)
    doc["dossiers"][0]["options"][0]["item"] = "TypeA|ALG-L|P1"
    other = scope(line=3)
    problems = validate_dossiers(doc, [scope(), other], GROUPS)
    assert any("not another member" in p for p in problems)
    assert any(f"{other.id}: neither a dossier nor in noOptions" in p for p in problems)


def test_the_command_writes_dossiers_from_a_recorded_run(run):  # noqa: F811
    app = run / "apps" / "demo"
    app.mkdir(parents=True)
    for name in ("scopes.json", "app.json"):
        shutil.copy(DEMO / name, app / name)
    doc = dossier(run, "demo", F / "app", **QUIET)
    [d] = doc["dossiers"]
    assert d["current"] == "Cipher|AES/GCM/NoPadding|Slow" and d["source"].startswith("    byte[] seal(")
    [option] = d["options"]
    time = next(e for e in option["estimates"] if e["metric"] == "timeNs")
    assert option["item"] == "Cipher|AES/GCM/NoPadding|Fast" and time["ratio"] < 0.4 and time["pImprove"] == 1.0
    assert {n["reason"] for n in doc["noOptions"]} == {"unresolved", "no_alternative"}
    assert validate_run(run)["apps/demo/dossiers.json"] == []
