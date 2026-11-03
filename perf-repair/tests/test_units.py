import re
import shutil
from pathlib import Path

import pytest

from perfrepair.dto.lifecycle import Lifecycle, Requirement, Step
from perfrepair.dto.site import Scope, scope_id
from perfrepair.dto.unit import Link, Unit, read_units, unit_id
from perfrepair.scope.build import build_scopes
from perfrepair.scope.units.build import build_units, unit_counts, units_document
from perfrepair.scope.units.relations import read_relations
from perfrepair.validation.units import validate_units

F = Path(__file__).parent / "fixtures" / "units"
CALL = re.compile(r"(\w+)\.getInstance\(\"([^\"]*)\"\)")


def sites(file: str) -> dict[str, dict]:
    out = {}
    for n, text in enumerate((F / file).read_text().splitlines(), 1):
        marker = re.search(r"// site: (\w+)", text)
        if marker:
            m = CALL.search(text)
            out[marker.group(1)] = {"file": file, "line": n, "call": m.group(0), "engineType": m.group(1),
                                    "resolvedAlgorithm": m.group(2), "resolvedProvider": "P1", "resolution": "explicit"}
    return out


@pytest.fixture
def java(tmp_path):
    pytest.importorskip("tree_sitter_java")
    return read_file(tmp_path, "Sealer.java")


@pytest.fixture
def kotlin(tmp_path):
    pytest.importorskip("tree_sitter_kotlin")
    return read_file(tmp_path, "Held.kt")


def read_file(tmp_path, file):
    shutil.copy(F / file, tmp_path / file)
    found = sites(file)
    scopes = build_scopes("demo", tmp_path, list(found.values())).scopes
    by_marker = {m: next(s for s in scopes if s.line == site["line"]) for m, site in found.items()}
    return by_marker, build_units("demo", scopes, tmp_path), scopes


def unit_of(units, scope):
    return next(u for u in units if scope.id in u.members)


def kinds(unit):
    return sorted((k.kind, k.via) for k in unit.links)


def test_a_key_made_once_ties_the_two_held_objects_and_their_producer(java):
    m, units, _ = java
    u = unit_of(units, m["seal"])
    assert set(u.members) == {m["factory"].id, m["seal"].id, m["open"].id}
    assert kinds(u) == [("inverse", "key"), ("producer_consumer", "line"), ("producer_consumer", "line"),
                        ("shared_key", "derived")]
    inverse = next(k for k in u.links if k.kind == "inverse")
    made = m["factory"].line + 1
    assert (inverse.a, inverse.b) == (m["seal"].id, m["open"].id)
    assert inverse.aLines == (made, m["seal"].line + 1) and inverse.bLines == (made, m["open"].line + 1)


def test_a_generator_returning_the_type_a_parameter_takes_feeds_the_inverse_pair(java):
    m, units, _ = java
    u = unit_of(units, m["fed_enc"])
    assert set(u.members) == {m["generator"].id, m["fed_enc"].id, m["fed_dec"].id}
    assert kinds(u) == [("inverse", "producer"), ("producer_consumer", "parameter"), ("producer_consumer", "parameter")]


def test_inverse_pair_taking_keys_from_callers_in_one_class_links_without_a_producer(java):
    m, units, _ = java
    u = unit_of(units, m["raw_enc"])
    assert set(u.members) == {m["raw_enc"].id, m["raw_dec"].id} and kinds(u) == [("inverse", "parameter")]


def test_two_independent_objects_in_one_function_stay_two_units_that_know_each_other(java):
    m, units, _ = java
    first, second = unit_of(units, m["mac_first"]), unit_of(units, m["mac_second"])
    assert first.id != second.id and first.links == () and second.links == ()
    assert first.sharedFunction == (second.id,) and second.sharedFunction == (first.id,)


def test_a_parameter_the_step_does_not_name_is_not_the_key(java):
    m, units, _ = java
    assert unit_of(units, m["signer"]).members == (m["signer"].id,)
    assert unit_of(units, m["pair"]).members == (m["pair"].id,)


def test_two_parameters_on_one_line_are_two_keys(java):
    m, units, _ = java
    assert unit_of(units, m["left"]).id != unit_of(units, m["right"]).id


def test_an_object_never_used_links_to_nothing(java):
    m, units, _ = java
    assert m["never"].lifecycle.status == "no_real_use"
    assert unit_of(units, m["never"]).members == (m["never"].id,)


def test_kotlin_helper_call_field_write_and_wrap_steps(kotlin):
    m, units, _ = kotlin
    helper = unit_of(units, m["kt_helper"])
    assert m["kt_generator"].id in helper.members
    assert ("producer_consumer", "call") in kinds(helper)
    held = unit_of(units, m["kt_held"])
    assert m["kt_field_generator"].id in held.members and ("producer_consumer", "field") in kinds(held)
    assert m["kt_wrap"].id in held.members
    assert read_relations().operations(m["kt_wrap"]) >= {"WRAP"}


def test_units_cover_every_scope_validate_and_round_trip(java):
    _, units, scopes = java
    doc = units_document("demo", units)
    assert validate_units(doc, [s.to_json() for s in scopes]) == []
    assert read_units(doc) == units
    counts = unit_counts(units)
    assert counts["units"] == len(units) and counts["largest"] == 3 and counts["links"]["inverse"] == 3


def test_units_are_stable_across_runs(java, tmp_path):
    _, units, scopes = java
    assert build_units("demo", list(reversed(scopes)), tmp_path) == units


def scope(line, *requirements, steps=(), status="bounded"):
    sid = scope_id("demo", "A.java", "f", line, "E.getInstance")
    return Scope(sid, "demo", "A.java", line, "E.getInstance", "f", 1, 90, "Cipher", "X", "P", "explicit",
                 lifecycle=Lifecycle(status, ("field",) if status == "partially_bounded" else (), "local", tuple(steps), tuple(requirements)))


def doc_of(*units):
    return {"schemaVersion": 1, "app": "demo", "units": [u.to_json() for u in units]}


A = scope(10, Requirement("key", "field", 3, 11), steps=[Step("use", "doFinal", 12, "same")])
B = scope(20, Requirement("key", "field", 3, 21), steps=[Step("use", "doFinal", 22, "same")])
SCOPES = [A.to_json(), B.to_json()]
GOOD = Link("shared_key", A.id, B.id, (3, 11), (3, 21), "field")


def pair(*links, members=(A.id, B.id)):
    return Unit(unit_id("demo", list(members)), tuple(members), tuple(links))


def test_validator_accepts_a_connected_unit():
    assert validate_units(doc_of(pair(GOOD)), SCOPES) == []


@pytest.mark.parametrize("doc, problem", [
    (doc_of(pair()), "not connected"),
    (doc_of(pair(Link("shared_key", A.id, B.id, (99,), (3,), "field"))), "line 99 is not in the lifecycle"),
    (doc_of(pair(Link("shared_key", A.id, B.id, (), (3,), "field"))), "cites no line"),
    (doc_of(pair(Link("other", A.id, B.id, (3,), (3,), "field"))), "is not in"),
    (doc_of(pair(Link("inverse", A.id, B.id, (3,), (3,), "field"))), "is not in"),
    (doc_of(pair(Link("shared_key", A.id, A.id, (3,), (3,), "field"))), "to itself"),
    (doc_of(Unit("0" * 12, (A.id, B.id), (GOOD,))), "id is not unit_id"),
    (doc_of(pair(GOOD, members=(A.id, B.id, "nope"))), "not in scopes.json"),
    (doc_of(pair(members=(A.id,))), "in no unit"),
    (doc_of(pair(GOOD), pair(members=(A.id,))), "in several units"),
    ({"schemaVersion": 9, "app": "demo", "units": []}, "schemaVersion 9"),
    ({"schemaVersion": 1, "app": "demo"}, "units is not a list"),
])
def test_validator_refuses(doc, problem):
    assert any(problem in p for p in validate_units(doc, SCOPES))


def test_validator_refuses_a_shared_function_of_no_unit():
    u = pair(GOOD)
    bad = Unit(u.id, u.members, u.links, ("gone",))
    assert any("sharedFunction" in p for p in validate_units(doc_of(bad), SCOPES))


def test_without_the_parser_every_scope_is_a_unit_of_one(tmp_path):
    unread = [Scope(scope_id("demo", "A.java", "f", n, "E.getInstance"), "demo", "A.java", n, "E.getInstance", "f", 1, 90,
                    "Cipher", "X", "P", "explicit", lifecycle=Lifecycle.unsupported("parser_missing")) for n in (10, 20)]
    units = build_units("demo", unread, tmp_path)
    assert [len(u.members) for u in units] == [1, 1] and all(not u.links for u in units)
