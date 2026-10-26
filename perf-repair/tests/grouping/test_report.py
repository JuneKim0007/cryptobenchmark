import json

import pytest
from grouping_data import FAMILIES
from conftest import CHARTER, QUIET, by_name

from perfrepair.dto.grouping import Item, Profile
from perfrepair.dto.grouping_state import Group, Knowledge
from perfrepair.ai.parse.grouping_assign.kind import GroupingKind
from perfrepair.ai.runtime.engine.decide import decide
from perfrepair.grouping.report.checks import report
from perfrepair.grouping.report.rules import check, common_key_sizes
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.validation import ValidationFailed
from perfrepair.validation.grouping.output import validate_output

ITEMS = {1: Item(1, "TypeC", "R/OAEP", "P1", "cipher.pair", "OAEP mgf1=SHA-1"),
         2: Item(2, "TypeC", "R/OAEP", "P2", "cipher.pair", "OAEP mgf1=SHA-256"),
         3: Item(3, "TypeC", "S/M", "P1", "cipher.secret"), 4: Item(4, "TypeC", "S/M", "P2", "cipher.secret"),
         5: Item(5, "TypeD", "H", "P1", "digest.none")}


def profile(runs=True, sizes=()):
    return Profile("pair", "measured", True, runs, preparedKeySizes=tuple(sizes))


PROFILES = {1: profile(sizes=(2048,)), 2: profile(sizes=(2048, 4096)), 3: profile(sizes=(128,)),
            4: profile(sizes=(256,)), 5: profile(runs=False)}
KNOWLEDGE = Knowledge(5, {"oaep": Group("cipher.pair", "rsa oaep", [1, 2]), "sym": Group("cipher.secret", "s", [3, 4]),
                          "h": Group("digest.none", "h", [5])}, [])


def test_rules_report_what_static_data_proves():
    kinds = {(f.kind, f.group) for f in check(KNOWLEDGE, ITEMS, PROFILES)}
    assert kinds == {("resolved_parameters_differ", "oaep"), ("no_common_key_size", "sym"),
                     ("no_runnable_member", "h"), ("singleton", "h")}
    assert common_key_sizes([1, 2], PROFILES) == [2048]


def test_a_dropped_item_is_an_error_finding():
    k = Knowledge(5, {"oaep": Group("cipher.pair", "x", [1, 2])}, [3])
    assert [f.kind for f in check(k, ITEMS, PROFILES) if f.severity == "error"] == ["resolved_parameters_differ", "dropped"]


def test_report_writes_validated_checks_and_groups(paths):
    decide(GroupingKind(paths, FAMILIES), CHARTER, ScriptedConversations(by_name), paths.root, **QUIET)
    document = report(paths, FAMILIES)
    assert json.loads(paths.groups.read_text()) == document
    assert {g["id"] for g in document["groups"]} >= {"alg-s-m1"}
    shared = next(g for g in document["groups"] if g["id"] == "alg-s-m1")
    assert shared["members"] == [3, 4] and shared["runnable"] == [3, 4]
    assert document["items"]["3"]["group"] == "alg-s-m1"
    assert "counts" in json.loads(paths.checks.read_text())


def test_report_refuses_an_unfinished_grouping(paths):
    from perfrepair.dto.grouping_state import Knowledge as K
    from perfrepair.files import write_json
    write_json(paths.knowledge, K().to_json())
    with pytest.raises(ValidationFailed, match="not decided yet"):
        report(paths, FAMILIES)


def test_output_validator_names_inconsistencies():
    doc = {"schemaVersion": 1, "families": {"cipher.pair": "x"},
           "groups": [{"id": "a", "family": "cipher.pair", "members": [1, 2]}, {"id": "b", "family": "cipher.secret", "members": [2]}],
           "items": {"1": {"qualified": ITEMS[1].qualified, "group": "a"}}, "dropped": [{"item": 1, "problems": []}]}
    problems = validate_output(doc, ITEMS)
    for expected in ("item 2: in 2 groups", "item 1: grouped and dropped", "item 5: neither grouped nor dropped",
                     "items index differs", "family cipher.secret is not listed"):
        assert any(expected in p for p in problems), expected
