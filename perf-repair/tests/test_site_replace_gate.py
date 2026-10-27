import json

import pytest
from site_replace_data import GOOD_EDITS, KEEP, PINS, answer, dossier, edit

from perfrepair.dto.site import Replacement
from perfrepair.validation.suggest.replace import check_reply

D = dossier()


def check(reply, d=D):
    return check_reply(reply if isinstance(reply, str) else json.dumps(reply), d)


def test_a_good_replace_maps_aliases_back_to_items_and_typed_pins():
    decision, problems = check(answer())
    r = Replacement.from_json(decision)
    assert problems == [] and r.option == "TypeA|ALG-A/MODE-X|P2" and r.scope == D.key
    assert [(e.kind, e.provider, e.parameters) for e in r.edits] == [
        ("set_provider", "P2", None), ("pin_parameters", None, {"ivLength": 12, "tagMode": "full"})]


def test_a_good_keep():
    decision, problems = check(KEEP)
    assert problems == [] and decision["decision"] == "keep" and decision["option"] is None


@pytest.mark.parametrize("reply, problem", [
    ("not json", "reply is not JSON"),
    ("[1]", "reply is not an object"),
    (answer("swap"), "decision 'swap' is not one of"),
    (answer(option="R9"), "option 'R9' is not one of R1, R2"),
    (answer(option="TypeA|ALG-A/MODE-X|P2"), "is not one of R1, R2"),
    (answer(edits=[]), "replace names no edit"),
    (answer("keep", "R1", []), "keep names option 'R1'"),
    (answer("keep", "", GOOD_EDITS), "keep names edits"),
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
    (answer(risks=["fast"]), "risk 'fast' is not one of"),
    (answer(risks=["wire_format", "wire_format"]), "risk 'wire_format' given more than once"),
    (answer(reason="  "), "reason is empty"),
    ({**answer(), "edits": "x"}, "edits is not a list"),
    ({**answer(), "option": None}, "option is not a string"),
])
def test_gate(reply, problem):
    decision, problems = check(reply)
    assert decision is None and any(problem in p for p in problems), problems


def test_a_replace_without_pins_needs_only_set_provider():
    decision, problems = check(answer(option="R2", edits=[edit("set_provider", "P3")], risks=[]))
    assert problems == [] and [e["kind"] for e in decision["edits"]] == ["set_provider"]


def test_messages_never_name_an_item_id_the_model_was_not_asked_for():
    _, problems = check(answer(option="R9", edits=[edit("set_provider", "P3")]))
    assert not any("|" in p for p in problems)
