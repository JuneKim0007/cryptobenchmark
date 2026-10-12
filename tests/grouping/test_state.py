
import pytest
from grouping_data import FAMILIES

from perfrepair.dto.grouping import Item
from perfrepair.dto.decision import OutboxRecord
from perfrepair.dto.grouping_state import Amendment, Answer, Knowledge
from perfrepair.grouping.state.cursor import cursor
from perfrepair.grouping.state.knowledge import apply
from perfrepair.validation.grouping.answer import parse_answer, validate_answer
from perfrepair.validation.grouping.knowledge import validate_knowledge

ITEMS = [Item(1, "TypeC", "A/M1", "P1", "cipher.secret"), Item(2, "TypeC", "A/M1", "P2", "cipher.secret"),
         Item(3, "TypeC", "B/M2", "P1", "cipher.secret"), Item(4, "TypeD", "H", "P1", "digest.none")]
BY_ID = {i.id: i for i in ITEMS}


def new(gid, text="one function"):
    return Answer(newGroupId=gid, newGroupDescription=text, reason="first of its kind")


def join(gid, amend=()):
    return Answer(group=gid, amend=amend, reason="same function")


def record(seq, item, answer=None, problems=()):
    return OutboxRecord(seq, str(item), "dropped" if answer is None else "decided", 1, 1,
                        answer.to_json() if answer else None, problems)


RECORDS = [record(1, 1, new("a-m1")), record(2, 2, join("a-m1", (Amendment("a-m1", "refined"),))), record(3, 3)]


def project(records, by_id):
    k = Knowledge()
    for r in records:
        apply(k, r, by_id[int(r.item)])
    return k


def test_projection_and_cursor():
    k = project(RECORDS, BY_ID)
    assert k.groups["a-m1"].members == [1, 2] and k.groups["a-m1"].description == "refined"
    assert k.dropped == [3] and k.version == 3
    c = cursor(ITEMS, RECORDS)
    assert (c.next, c.decided, c.dropped, c.knowledgeVersion) == (4, 2, 1, 3)
    assert cursor(ITEMS, RECORDS + [record(4, 4, new("h"))]).next is None


def test_knowledge_structure_is_checked():
    k = project(RECORDS, BY_ID)
    assert validate_knowledge(k, BY_ID, FAMILIES) == []
    k.groups["a-m1"].members.append(4)
    assert any("member 4 is in family digest.none" in p for p in validate_knowledge(k, BY_ID, FAMILIES))


@pytest.mark.parametrize("answer, problem", [
    (Answer(reason="r"), "exactly one of"),
    (Answer(group="a-m1", newGroupId="x", newGroupDescription="d", reason="r"), "exactly one of"),
    (join("nope"), "is not a group of family"),
    (new("Bad Id"), "must match"),
    (new("a-m1"), "already exists"),
    (new("cipher.secret"), "is a family id"),
    (new("ok-id", text=""), "description is empty"),
    (new("ok-id", text="x" * 401), "more than 400"),
    (join("a-m1", (Amendment("a-m1", "a"), Amendment("a-m1", "b"))), "names a group twice"),
    (Answer(group="a-m1", reason=""), "reason is empty"),
])
def test_answer_gate_names_the_broken_rule(answer, problem):
    k = project(RECORDS[:1], BY_ID)
    problems = validate_answer(answer, ITEMS[2], k, FAMILIES)
    assert any(problem in p for p in problems), problems


def test_answer_cannot_cross_families_or_redecide():
    k = project(RECORDS[:1], BY_ID)
    assert any("not a group of family digest.none" in p for p in validate_answer(join("a-m1"), ITEMS[3], k, FAMILIES))
    assert any("already decided" in p for p in validate_answer(join("a-m1"), ITEMS[0], k, FAMILIES))
    assert validate_answer(join("a-m1"), ITEMS[2], k, FAMILIES) == []


def test_parse_answer_refuses_wrong_shapes():
    assert parse_answer("nope")[1][0].startswith("reply is not JSON")
    assert "amend is not a list" in parse_answer('{"group": "x", "amend": [1], "reason": "r"}')[1][0]
    answer, problems = parse_answer('{"group": " a-m1 ", "newGroup": {"id": "", "description": ""}, "amend": [], "reason": "r"}')
    assert problems == [] and answer.group == "a-m1"
