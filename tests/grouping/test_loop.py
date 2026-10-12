import json

import pytest
from conftest import QUIET, Remembering, by_name, item_name
from grouping_data import FAMILIES

from perfrepair.grouping.loop.run import Limits, run
from perfrepair.grouping.state.outbox import Outbox
from perfrepair.orchestrate.agent import AgentRefused, ScriptedConversations

def records(paths):
    return Outbox(paths.outbox).open().records()


def test_every_item_gets_one_fresh_conversation_and_a_committed_outcome(paths):
    agent = ScriptedConversations(by_name)
    knowledge = run(paths, agent, FAMILIES, **QUIET)
    assert agent.started == 6 and len(records(paths)) == 6
    assert knowledge.groups["alg-s-m1"].members == [3, 4]
    assert json.loads(paths.cursor.read_text())["next"] is None
    assert json.loads(paths.knowledge.read_text()) == knowledge.to_json()
    first_messages = [m for _, turn, m in agent.turns if turn == 1]
    assert all(m.count("ITEM") == 1 for m in first_messages)
    assert all("digests" not in m for m in first_messages if "cipher" in m.split("—")[0])


def test_a_rejected_answer_is_corrected_in_the_same_conversation(paths):
    def answer(message, conversation, turn):
        return "not json" if turn == 1 else by_name(message)
    agent = ScriptedConversations(Remembering(answer))
    run(paths, agent, FAMILIES, **QUIET)
    assert agent.started == 6
    assert all("YOUR ANSWER WAS REJECTED" in m for _, turn, m in agent.turns if turn == 2)
    statuses = [json.loads(line)["status"] for line in paths.journal.read_text().splitlines()]
    assert statuses[:2] == ["rejected", "accepted"]


def test_three_rejections_respawn_a_fresh_conversation(paths):
    def answer(message, conversation, turn):
        return {"group": "ghost", "newGroup": {"id": "", "description": ""}, "amend": [], "reason": "x"} \
            if conversation % 2 == 1 else by_name(message)
    agent = ScriptedConversations(answer)
    run(paths, agent, FAMILIES, Limits(turns=3, sessions=2), **QUIET)
    assert agent.started == 12
    assert all(r.session == 2 and r.turn == 1 for r in records(paths))


def test_an_item_no_conversation_answers_is_dropped_and_the_run_continues(paths):
    def answer(message, conversation, turn):
        if item_name(message) == "H1":
            raise AgentRefused("declined")
        return by_name(message)
    knowledge = run(paths, ScriptedConversations(Remembering(answer)), FAMILIES, Limits(turns=2, sessions=2), **QUIET)
    dropped = [r for r in records(paths) if r.outcome == "dropped"]
    assert len(dropped) == 1 and len(dropped[0].problems) == 4 and knowledge.dropped == [dropped[0].item]
    errors = [json.loads(line) for line in paths.errors.read_text().splitlines()]
    assert errors[0]["qualified"].startswith("TypeD|H1") and "model refused: declined" in errors[0]["problems"][0]


def test_a_crash_resumes_without_losing_or_repeating_a_decision(paths):
    calls = {"n": 0}

    def flaky(message, *_):
        calls["n"] += 1
        if calls["n"] == 4:
            raise RuntimeError("connection lost")
        return by_name(message)
    with pytest.raises(RuntimeError):
        run(paths, ScriptedConversations(flaky), FAMILIES, **QUIET)
    assert len(records(paths)) == 3
    (paths.outbox / ".tmp-000004.json").write_text("{half written")
    agent = ScriptedConversations(by_name)
    knowledge = run(paths, agent, FAMILIES, **QUIET)
    assert agent.started == 3 and len(records(paths)) == 6
    assert sorted(m for g in knowledge.groups.values() for m in g.members) == [1, 2, 3, 4, 5, 6]
