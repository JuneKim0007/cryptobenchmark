from dataclasses import replace

import pytest
from conftest import LIBRARY, QUIET, by_name
from grouping_data import FAMILIES
from test_code_groups import screen

from perfrepair import run_dir as rd
from perfrepair.ai.parse.grouping_assign.kind import GroupingKind, charter
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.runtime.engine.decide import decide
from perfrepair.device.used import used_set, write_used
from perfrepair.dto.grouping import profiles_document, read_profiles
from perfrepair.dto.signature import Component, Signature
from perfrepair.dto.used import UsedItem, UsedSet
from perfrepair.files import read_json, write_json
from perfrepair.grouping.report.checks import report
from perfrepair.validation import ValidationFailed
from perfrepair.validation.used import validate_used

S_M1_P1, S_M1_P2, RAW, PAIR, PASSWORD, H1 = ("TypeC|ALG-S/M1|P1", "TypeC|ALG-S/M1|P2", "TypeC|ALG-RAW|P1",
                                             "TypeC|ALG-P/X|P1", "TypeC|PASSWORD-ALG|P2", "TypeD|H1|P1")


def site(qualified):
    engine_type, name, provider = qualified.split("|")
    return {"engineType": engine_type, "resolvedAlgorithm": name, "resolvedProvider": provider}


def app(paths, name, *qualified, unresolved=0):
    folder = rd.app_dir(paths.root.parent, name)
    folder.mkdir(exist_ok=True)
    sites = [site(q) for q in qualified] + [{"engineType": "TypeC", "resolvedAlgorithm": None, "resolvedProvider": None}] * unresolved
    write_json(folder / rd.SITES, {"sites": sites})
    return name


def via(used):
    return {u.item: u.via for u in used.items}


def assign(paths):
    kind = GroupingKind(paths, FAMILIES)
    agent = ScriptedConversations(by_name)
    decide(kind, charter(LIBRARY, kind.inputs), agent, paths.root, **QUIET)
    return agent.started


def test_a_site_brings_its_code_group_and_nothing_else(paths):
    screen(paths)
    used = used_set(paths.root.parent, [app(paths, "a1", S_M1_P1, unresolved=2)])
    assert via(used) == {S_M1_P1: "site", S_M1_P2: "group"}
    assert used.apps["a1"].sites == 3 and used.apps["a1"].matched == 1 and used.deviceItems == 6


def test_an_item_with_no_record_brings_the_askable_items_of_its_family_it_could_join(paths):
    used = used_set(paths.root.parent, [app(paths, "a1", S_M1_P1)])
    assert via(used) == {S_M1_P1: "site", S_M1_P2: "candidate", RAW: "candidate"}


def test_a_known_component_both_sides_differ_on_keeps_an_item_out(paths):
    profiles = read_profiles(read_json(paths.profiles))
    for n, value in ((2, "raw"), (3, "s")):
        profiles[n] = replace(profiles[n], signature=Signature((Component("name", value),)))
    write_json(paths.profiles, profiles_document(profiles))
    assert RAW not in via(used_set(paths.root.parent, [app(paths, "a1", S_M1_P1)]))


def test_used_json_narrows_what_is_asked_and_the_rest_is_not_used_never_dropped(paths):
    write_used(paths.root.parent, [app(paths, "a1", S_M1_P1)])
    assert assign(paths) == 3
    doc = report(paths, FAMILIES)
    assert doc["notUsed"] == [1, 5, 6] and doc["dropped"] == []


def test_a_new_target_asks_only_its_new_items_and_a_removed_one_keeps_its_groups(paths):
    write_used(paths.root.parent, [app(paths, "a1", S_M1_P1)])
    assign(paths)
    kept = {e["qualified"]: e["group"] for e in report(paths, FAMILIES)["items"].values() if e["group"]}
    write_used(paths.root.parent, ["a1", app(paths, "a2", H1)])
    assert assign(paths) == 1
    write_used(paths.root.parent, ["a2"])
    assert assign(paths) == 0
    doc = report(paths, FAMILIES)
    assert {q: g for q, g in ((e["qualified"], e["group"]) for e in doc["items"].values()) if q in kept} == kept
    assert doc["notUsed"] == [1, 5]


def test_without_used_json_every_askable_item_is_asked_and_no_not_used_list(paths):
    assert assign(paths) == 6 and "notUsed" not in report(paths, FAMILIES)


def test_the_validator_names_a_foreign_item_and_an_unlisted_app():
    used = UsedSet(1, {}, (UsedItem("T|X|P", "site", ("ghost",)), UsedItem("T|X|P", "odd", ())))
    problems = validate_used(used, {"T|Y|P"})
    assert "item T|X|P: listed 2 times" in problems and "item T|X|P: not in items.json" in problems
    assert "item T|X|P: app ghost is not listed" in problems and "item T|X|P: no app needs it" in problems
    assert any("via 'odd'" in p for p in problems)


def test_write_used_refuses_what_its_validator_refuses(paths, monkeypatch):
    monkeypatch.setattr("perfrepair.device.used.validate_used", lambda *_: ["bad"])
    with pytest.raises(ValidationFailed):
        write_used(paths.root.parent, [app(paths, "a1", S_M1_P1)])
    assert not (paths.root.parent / rd.USED).exists()
