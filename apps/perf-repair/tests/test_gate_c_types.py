"""Gate C on a reply of the wrong types: every field of a good reply swapped for each wrong type is a result, never a raise,
so the model gets its correction turn."""
import copy
import json

import pytest
from site_replace_data import answer, dossier, item
from test_worthiness_kind import G, KIND, P1, P2

from perfrepair.dto import Verdicts
from perfrepair.validation.parse.grouping_assign import parse_answer
from perfrepair.validation.review.grouping_review import parse_review
from perfrepair.validation.suggest.site_replace import check_reply

WRONG = ([], [[]], [{}], {}, {"a": 1}, 1, 1.5, True, None, "x")
GROUPS = {"a": [1], "b": [2]}
FINDING = {"findings": [{"kind": "merge", "groups": ["a", "b"], "items": [1, 2], "reason": "r"}]}
ANSWER = {"group": "", "newGroup": {"id": "new-group", "description": "d"},
          "amend": [{"group": "a", "description": "d"}], "reason": "r"}
PAIRS = {"decision": "test", "pairs": [{"from": P1, "to": P2, "reason": "r"}], "reason": "r"}
UNIT = item(dossier())


def paths(value, at=()):
    """The path of every value inside a reply, the reply's own fields and all they hold."""
    children = value.items() if isinstance(value, dict) else enumerate(value) if isinstance(value, list) else ()
    for key, child in children:
        yield (*at, key)
        yield from paths(child, (*at, key))


def swapped(doc, path, wrong):
    doc = copy.deepcopy(doc)
    held = doc
    for key in path[:-1]:
        held = held[key]
    held[path[-1]] = wrong
    return json.dumps(doc)


GATES = {
    "review": (lambda text: parse_review(text, GROUPS), FINDING),
    "worthiness": (lambda text: KIND.check(G, text, Verdicts("latency")), PAIRS),
    "replace": (lambda text: check_reply(text, UNIT), answer()),
    "recommend": (lambda text: check_reply(text, UNIT), answer("recommend")),
    "assign": (parse_answer, ANSWER),
}


@pytest.mark.parametrize("gate", GATES)
def test_a_wrong_type_anywhere_in_a_reply_is_a_result_never_a_raise(gate):
    check, good = GATES[gate]
    for path in paths(good):
        for wrong in WRONG:
            decision, problems = check(swapped(good, path, wrong))
            assert (decision is None) == bool(problems), (path, wrong)


@pytest.mark.parametrize("check, reply", [
    (GATES["review"][0], {"findings": [{"kind": "merge", "groups": [["a"], "b"], "items": [], "reason": "r"}]}),
    (GATES["review"][0], {"findings": [{"kind": "misplaced", "groups": ["a", "b"], "items": [[1]], "reason": "r"}]}),
    (GATES["worthiness"][0], {"decision": "test", "pairs": [{"from": [P1], "to": P2, "reason": "r"}], "reason": "r"}),
    (GATES["replace"][0], {"decision": "replace", "members": [{"member": ["S1"]}], "reason": "r"}),
    (parse_answer, {"newGroup": {"id": 7, "description": "d"}, "reason": "r"}),
])
def test_the_types_a_schema_should_forbid_are_problems_for_the_retry(check, reply):
    decision, problems = check(json.dumps(reply))
    assert decision is None and problems
