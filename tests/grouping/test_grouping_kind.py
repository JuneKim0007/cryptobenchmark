import json

import pytest
from conftest import QUIET, Remembering, by_name, item_name
from grouping_data import FAMILIES

from perfrepair.files import write_json
from perfrepair.grouping.kind import GroupingKind
from perfrepair.grouping.prompt.render import system_prompt
from perfrepair.orchestrate.agent import AgentRefused, ScriptedConversations
from perfrepair.orchestrate.engine.ask import Limits
from perfrepair.orchestrate.engine.decide import decide
from perfrepair.orchestrate.engine.outbox import Outbox
from perfrepair.validation import ValidationFailed
from perfrepair.validation.grouping.answer import MAX_DESCRIPTION, SLUG


def group(paths, agent, limits=Limits(), limit=None):
    return decide(GroupingKind(paths, FAMILIES), agent, paths.root, limits, limit, **QUIET)


def records(paths):
    return Outbox(paths.outbox).records()


def test_every_item_gets_one_fresh_conversation_and_a_committed_outcome(paths):
    agent = ScriptedConversations(by_name)
    knowledge = group(paths, agent)
    assert agent.started == 6 and len(records(paths)) == 6
    assert knowledge.groups["alg-s-m1"].members == [3, 4]
    assert json.loads(paths.cursor.read_text())["next"] is None
    assert json.loads(paths.knowledge.read_text()) == knowledge.to_json()
    first = [m for _, turn, m in agent.turns if turn == 1]
    assert all(m.count("ITEM") == 1 for m in first)


def test_a_rejected_answer_is_corrected_in_the_same_conversation(paths):
    agent = ScriptedConversations(Remembering(lambda m, c, turn: "not json" if turn == 1 else by_name(m)))
    group(paths, agent)
    assert agent.started == 6
    statuses = [json.loads(line)["status"] for line in (paths.root / "journal.jsonl").read_text().splitlines()]
    assert statuses[:2] == ["rejected", "accepted"]


def test_an_item_no_conversation_answers_is_dropped_and_the_run_continues(paths):
    def answer(m, c, t):
        if item_name(m) == "H1":
            raise AgentRefused("declined")
        return by_name(m)
    knowledge = group(paths, ScriptedConversations(Remembering(answer)), Limits(turns=2, sessions=2))
    dropped = [r for r in records(paths) if r.outcome == "dropped"]
    assert len(dropped) == 1 and knowledge.dropped == [int(dropped[0].item)]
    errors = [json.loads(line) for line in paths.errors.read_text().splitlines()]
    assert errors[0]["label"].startswith("TypeD|H1") and "model refused: declined" in errors[0]["problems"][0]


def test_a_crash_resumes_without_losing_or_repeating_a_decision(paths):
    calls = {"n": 0}

    def flaky(m, *_):
        calls["n"] += 1
        if calls["n"] == 4:
            raise RuntimeError("connection lost")
        return by_name(m)
    with pytest.raises(RuntimeError):
        group(paths, ScriptedConversations(flaky))
    agent = ScriptedConversations(by_name)
    knowledge = group(paths, agent)
    assert agent.started == 3 and len(records(paths)) == 6
    assert sorted(m for g in knowledge.groups.values() for m in g.members) == [1, 2, 3, 4, 5, 6]


def test_a_tampered_items_file_is_refused_at_pop(paths):
    doc = json.loads(paths.items.read_text())
    doc["items"][0]["group"] = "smuggled"
    write_json(paths.items, doc)
    with pytest.raises(ValidationFailed):
        group(paths, ScriptedConversations(by_name))


def test_the_system_prompt_states_the_limits_the_gate_enforces():
    prompt = " ".join(system_prompt().split())
    assert f"at most {MAX_DESCRIPTION} characters" in prompt and SLUG.pattern in prompt
    assert "{max_description}" not in prompt and "{id_pattern}" not in prompt
