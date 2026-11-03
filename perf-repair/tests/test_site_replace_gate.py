import json

import pytest
from site_replace_data import GOOD_EDITS, KEEP, PINS, answer, dossier, edit, item, linked, member, scope

from perfrepair.dto.site import Option, Replacement, required_risks
from perfrepair.dto.unit import PairInterop, Stay, UnitDossiers
from perfrepair.validation.suggest.site_replace import check_reply

D = dossier()


def check(reply, d=D):
    return check_reply(reply if isinstance(reply, str) else json.dumps(reply), item(d))


def test_a_good_replace_maps_aliases_back_to_items_and_typed_pins():
    decision, problems = check(answer())
    r = Replacement.from_json(decision["replacements"][0])
    assert problems == [] and r.option == "TypeA|ALG-A/MODE-X|P2" and r.scope == D.key
    assert [(e.kind, e.provider, e.parameters) for e in r.edits] == [
        ("set_provider", "P2", None), ("pin_parameters", None, {"ivLength": 12, "tagMode": "full"})]


def test_a_good_keep():
    decision, problems = check(KEEP)
    [row] = decision["replacements"]
    assert problems == [] and row["decision"] == "keep" and row["option"] is None and row["scope"] == D.key


@pytest.mark.parametrize("reply, problem", [
    ("not json", "reply is not JSON"),
    ("[1]", "reply is not an object"),
    (answer("swap"), "decision 'swap' is not one of"),
    (answer(option="R9"), "option 'R9' is not one of R1, R2"),
    (answer(option="TypeA|ALG-A/MODE-X|P2"), "is not one of R1, R2"),
    (answer(edits=[]), "replace names no edit"),
    (answer("keep", "R1", []), "keep names members"),
    ({"decision": "replace", "members": [], "reason": "x"}, "replace covers every member with options: S1 is missing"),
    ({"decision": "replace", "members": [member("S7")], "reason": "x"}, "member 'S7' is not one of S1"),
    ({"decision": "replace", "members": [member(), member()], "reason": "x"}, "member S1 given more than once"),
    ({"decision": "replace", "members": "S1", "reason": "x"}, "members is not a list"),
    (answer(edits=GOOD_EDITS + [edit("rewrite_call")]), "kind 'rewrite_call' is not one of"),
    (answer(edits=GOOD_EDITS + [edit("set_provider", "P2")]), "set_provider given more than once"),
    (answer(edits=[edit("set_provider", "P3"), GOOD_EDITS[1]]), "set_provider names 'P3', but R1 is provided by 'P2'"),
    (answer(edits=[edit("set_provider", "P2", [("x", "1")]), GOOD_EDITS[1]]), "set_provider takes no parameters"),
    (answer(edits=[GOOD_EDITS[0]]), "R1 lists pins; pin_parameters must state them"),
    (answer(edits=[GOOD_EDITS[1]]), "set_provider must name it"),
    (answer(edits=[GOOD_EDITS[0], edit("pin_parameters", parameters=PINS[:1])]), "pin 'tagMode' of R1 is missing"),
    (answer(edits=[GOOD_EDITS[0], edit("pin_parameters", parameters=PINS + (("extra", "1"),))]),
     "'extra' is not a pin of R1"),
    (answer(edits=[GOOD_EDITS[0], edit("pin_parameters", parameters=(("ivLength", "16"), PINS[1]))]),
     "pin 'ivLength' is '16', but R1 lists '12'"),
    (answer(edits=[GOOD_EDITS[0], edit("pin_parameters", "P2", PINS)]), "pin_parameters takes no provider"),
    (answer(option="R2", edits=[edit("set_provider", "P3"), edit("pin_parameters", parameters=PINS)]),
     "pin_parameters on R2, which lists no pins"),
    (answer(edits=[edit("set_provider", "P2", algorithm="ALG-A/MODE-X"), GOOD_EDITS[1]]),
     "set_provider takes no algorithm"),
    (answer(option="R3", edits=[]), "replace names no edit"),
    (answer(option="R3", edits=[edit("set_algorithm", algorithm="ALG-C")]), "set_algorithm names 'ALG-C', but R3 is named 'ALG-B'"),
    (answer(option="R3", edits=[edit("set_provider", "P1")]), "R3 is named 'ALG-B', not the current 'ALG-A/MODE-X'; set_algorithm must name it"),
    (answer(option="R3", edits=[edit("set_algorithm", "P1", algorithm="ALG-B")]), "set_algorithm takes no provider"),
    (answer(edits=[GOOD_EDITS[0], {**edit("pin_parameters", parameters=PINS), "algorithm": None}]), "algorithm is not a string"),
    (answer(risks=["persisted_data"]), "risks must include key_compatibility: the key lives in a key store"),
    (answer(risks=[]), "risks must include persisted_data: the output is stored and read back later"),
    (answer(risks=["fast"]), "risk 'fast' is not one of"),
    (answer(risks=["wire_format", "wire_format"]), "risk 'wire_format' given more than once"),
    (answer(reason="  "), "reason is empty"),
    ({**answer(), "members": [{**member(), "edits": "x"}]}, "S1: edits is not a list"),
    ({**answer(), "members": [{**member(), "risks": None}]}, "S1: risks is not a list"),
    ({**answer(), "members": [{**member(), "option": None}]}, "S1: option None is not one of"),
])
def test_gate(reply, problem):
    decision, problems = check(reply)
    assert decision is None and any(problem in p for p in problems), problems


def test_a_replace_without_pins_needs_only_set_provider():
    decision, problems = check(answer(option="R2", edits=[edit("set_provider", "P3")]))
    assert problems == [] and [e["kind"] for e in decision["replacements"][0]["edits"]] == ["set_provider"]


def test_messages_never_name_an_item_id_the_model_was_not_asked_for():
    _, problems = check(answer(option="R9", edits=[edit("set_provider", "P3")]))
    assert not any("|" in p for p in problems)


def test_set_algorithm_resolves_to_the_option_name():
    decision, problems = check(answer(option="R3", edits=[edit("set_algorithm", algorithm="ALG-B")],
                                      risks=("persisted_data", "key_compatibility", "unverified_interop")))
    assert problems == [] and decision["replacements"][0]["edits"] == [
        {"kind": "set_algorithm", "provider": None, "algorithm": "ALG-B", "parameters": None}]


def test_the_model_may_add_risks_beyond_the_derived_ones():
    _, problems = check(answer(risks=["persisted_data", "key_compatibility", "wire_format"]))
    assert problems == []


def test_a_keep_need_not_declare_derived_risks():
    assert check(KEEP)[1] == []


@pytest.mark.parametrize("sinks, key_source, risks", [
    (("persist",), "keystore", {"persisted_data", "key_compatibility"}),
    (("network", "return"), "generated", {"wire_format"}),
    (("unknown",), "literal", {"unknown_sink", "key_compatibility"}),
    (("local",), "derived", set()),
])
def test_required_risks_come_from_the_scope_facts(sinks, key_source, risks):
    assert set(required_risks(scope(sinks=sinks, key_source=key_source))) == risks


def test_an_option_with_unknown_pins_cannot_be_replaced_to():
    unknown = dossier(options=(Option("R1", "TypeA|ALG-A/MODE-X|P2", None, "pass"),))
    decision, problems = check(answer(edits=[edit("set_provider", "P2")]), unknown)
    assert decision is None and any("R1 has unknown pins" in p for p in problems), problems
    assert check(KEEP, unknown)[1] == []


def test_a_replace_to_an_option_whose_interop_is_not_pass_must_declare_unverified_interop():
    _, problems = check(answer(option="R3", edits=[edit("set_algorithm", algorithm="ALG-B")]))
    assert problems == ["S1: risks must include unverified_interop: no interop check has run"]


@pytest.mark.parametrize("status, risks", [("pass", set()), ("not_checkable", {"unverified_interop"}),
                                           ("not_planned", {"unverified_interop"}), ("not_run", {"unverified_interop"})])
def test_required_risks_add_the_options_interop(status, risks):
    s = scope(sinks=("local",), key_source="derived")
    assert set(required_risks(s, Option("R1", "TypeA|ALG-B|P1", {}, status))) == risks


SECOND = dossier(file="src/Other.kt", options=(Option("R1", "TypeA|ALG-A/MODE-X|P3", {}, "pass"),),
                 sinks=("local",), key_source="derived")
PAIR = UnitDossiers(linked(D, SECOND), (D, SECOND), pairs=(PairInterop("TypeA|ALG-A/MODE-X|P2", "TypeA|ALG-A/MODE-X|P3", "pass"),))


def both(first=None, second=None):
    return {"decision": "replace", "reason": "timeNs ratio 0.62, pImprove 0.99",
            "members": [first or member(), second or member("S2", edits=[edit("set_provider", "P3")], risks=())]}


def test_a_unit_answer_gives_one_row_per_member_each_with_its_own_option():
    decision, problems = check_reply(json.dumps(both()), PAIR)
    rows = decision["replacements"]
    assert problems == [] and [(r["scope"], r["option"]) for r in rows] == [
        (D.key, "TypeA|ALG-A/MODE-X|P2"), (SECOND.key, "TypeA|ALG-A/MODE-X|P3")]
    assert {r["reason"] for r in rows} == {"timeNs ratio 0.62, pImprove 0.99"}


def test_a_unit_keep_is_one_row_per_member():
    decision, problems = check_reply(json.dumps(KEEP), PAIR)
    assert problems == [] and [(r["scope"], r["decision"]) for r in decision["replacements"]] == [
        (D.key, "keep"), (SECOND.key, "keep")]


@pytest.mark.parametrize("reply, problem", [
    ({**both(), "members": [member()]}, "replace covers every member with options: S2 is missing"),
    (both(second=member("S2", option="R2", edits=[edit("set_provider", "P3")], risks=())), "S2: option 'R2' is not one of R1"),
    (both(second=member("S2", risks=())), "pin_parameters on R1, which lists no pins"),
    (both(first=member(risks=())), "S1: risks must include"),
])
def test_a_unit_answer_is_checked_member_by_member(reply, problem):
    decision, problems = check_reply(json.dumps(reply), PAIR)
    assert decision is None and any(problem in p for p in problems), problems


STAYING = dossier(file="src/Stays.kt", options=())


def staying(*pairs):
    """D with options, its inverse partner S2 without: S2 stays on P1."""
    return UnitDossiers(linked(D, STAYING), (D,), (Stay(STAYING.key, STAYING.current, "no_alternative"),), pairs)


def test_a_member_without_options_stays_and_the_other_is_replaced_alone():
    unit = staying(PairInterop("TypeA|ALG-A/MODE-X|P1", "TypeA|ALG-A/MODE-X|P2", "pass"))
    decision, problems = check_reply(json.dumps(answer()), unit)
    assert problems == [] and [(r["scope"], r["decision"]) for r in decision["replacements"]] == [(D.key, "replace")]


def test_a_keep_covers_only_the_members_with_options():
    decision, problems = check_reply(json.dumps(KEEP), staying())
    assert problems == [] and [r["scope"] for r in decision["replacements"]] == [D.key]


def test_a_member_that_stays_is_never_named():
    reply = {**answer(), "members": [member(), member("S2")]}
    _, problems = check_reply(json.dumps(reply), staying())
    assert "member S2 has no option; it stays on TypeA|ALG-A/MODE-X|P1" in problems


@pytest.mark.parametrize("status, problem", [
    ("not_run", "S1: risks must include unverified_interop: its inverse S2 ends on TypeA|ALG-A/MODE-X|P1, and their "
                "interop is not_run"),
    ("fail", "S1 and S2 are inverse, and TypeA|ALG-A/MODE-X|P2 and TypeA|ALG-A/MODE-X|P1 failed their interop check"),
])
def test_an_inverse_pair_with_one_side_swapped_needs_the_interop_of_the_two_providers(status, problem):
    unit = staying(PairInterop("TypeA|ALG-A/MODE-X|P1", "TypeA|ALG-A/MODE-X|P2", status))
    decision, problems = check_reply(json.dumps(answer()), unit)
    assert decision is None and problems == [problem]
    if status == "not_run":
        risks = ("persisted_data", "key_compatibility", "unverified_interop")
        assert check_reply(json.dumps(answer(risks=risks)), unit)[1] == []


def test_two_sides_swapped_to_different_providers_need_their_interop_too():
    unchecked = UnitDossiers(PAIR.unit, PAIR.dossiers)
    _, problems = check_reply(json.dumps(both()), unchecked)
    assert problems == ["S1: risks must include unverified_interop: its inverse S2 ends on TypeA|ALG-A/MODE-X|P3, and "
                        "their interop is not_planned",
                        "S2: risks must include unverified_interop: its inverse S1 ends on TypeA|ALG-A/MODE-X|P2, and "
                        "their interop is not_planned"]
