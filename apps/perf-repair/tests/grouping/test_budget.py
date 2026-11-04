"""The per-role token budget: under, over then prefiltered, over and stopped; the prefilter hides only what gate C refuses."""
import argparse
import json
from dataclasses import replace

import pytest
import yaml
from conftest import CHARTER, LIBRARY, QUIET, by_name
from grouping_data import FAMILIES

from perfrepair.ai.parse.grouping_assign.kind import GroupingKind
from perfrepair.ai.review.grouping_review import command as review_cmd
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.runtime.engine.ask import Limits, ask
from perfrepair.ai.runtime.engine.budget import Budget, OverBudget, measure
from perfrepair.ai.runtime.engine.decide import decide
from perfrepair.ai.runtime.gateway.spawn import spawn
from perfrepair.config.load import load
from perfrepair.dto.grouping_state import Group, Knowledge
from perfrepair.dto.prompt import TaskPrompt
from perfrepair.dto.signature import CONVENTION, KNOWN, UNKNOWN, Component, Signature
from perfrepair.failure import reported
from perfrepair.grouping.report.checks import report
from perfrepair.inputs.table import GROUPING_SUPERVISOR
from perfrepair.log import attach
from perfrepair.log.read import read_events
from perfrepair.stop import CODES

KEY = "device.grouping.assign.budget"
MANY = 200


def scripted(answer, tokens=None, key=KEY):
    conversations = ScriptedConversations(answer)
    conversations.budget = None if tokens is None else Budget(key, tokens)
    return conversations


def sig(value, status=KNOWN):
    return Signature((Component("mode", value, status),))


def join(gid):
    return {"group": gid, "newGroup": {"id": "", "description": ""}, "amend": [], "reason": "same"}


class Scene:
    """An item, and a family's groups with one member each: its fact agrees, contradicts, is unknown, assumed or absent."""

    def __init__(self, paths):
        self.kind = GroupingKind(paths, FAMILIES)
        self.item = next(i for i in self.kind.pending() if i.family == "cipher.secret")
        others = [i.id for i in self.kind.items() if i.id != self.item.id][:5]
        facts = {"same": sig("M1"), "other": sig("M2"), "unknown": sig("M2", UNKNOWN), "assumed": sig("M2", CONVENTION), "none": None}
        self.kind.profiles[self.item.id] = replace(self.kind.profiles[self.item.id], signature=sig("M1"))
        self.knowledge = Knowledge(groups={})
        for member, (gid, fact) in zip(others, facts.items()):
            self.kind.profiles[member] = replace(self.kind.profiles[member], signature=fact)
            self.knowledge.groups[gid] = Group("cipher.secret", gid * MANY, [member])

    def shown(self, message):
        return {g["id"] for g in yaml.safe_load(message.text)["groups"]}


@pytest.fixture
def scene(paths):
    return Scene(paths)


def test_under_budget_the_whole_message_goes_and_the_size_is_journalled(paths, tmp_path):
    attach()
    attach(tmp_path)
    decide(GroupingKind(paths, FAMILIES), CHARTER, scripted(by_name, 100000), paths.root, **QUIET)
    lines = [json.loads(line) for line in paths.journal.read_text().splitlines()]
    assert lines and all(line["promptTokens"] > len(CHARTER.system.text) // 4 for line in lines)
    events = list(read_events(tmp_path / "log" / "events.jsonl"))
    decisions = [e for e in events if e.event == "decision"]
    assert decisions and all(e.data["promptTokens"] and "narrowedFrom" not in e.data for e in decisions)
    assert all(e.data["promptTokens"] for e in events if e.event == "turn")


def test_the_size_is_the_system_prompt_plus_the_message_by_chars_over_four():
    assert measure(CHARTER.system, TaskPrompt("n", "x" * 8, "i")) == (len(CHARTER.system.text) + 8 + 3) // 4


def test_over_budget_assign_is_prefiltered_and_the_narrowed_message_is_sent(scene):
    whole = scene.kind.render(scene.item, scene.knowledge)
    narrow = scene.kind.narrowed(scene.item, scene.knowledge)
    budget = measure(CHARTER.system, narrow)
    assert budget < measure(CHARTER.system, whole)
    sent = []
    asked = ask(scripted(lambda m, *_: sent.append(m) or join("same"), budget), CHARTER, whole,
                lambda text: (json.loads(text), []), Limits(), narrow=lambda: narrow)
    assert sent == [narrow] and asked.narrowedFrom == measure(CHARTER.system, whole)
    assert asked.last.promptTokens == budget


def test_a_narrowed_decision_records_the_size_it_came_from(paths, tmp_path):
    attach()
    attach(tmp_path)
    kind = GroupingKind(paths, FAMILIES)
    conversations = scripted(by_name, measure(CHARTER.system, TaskPrompt("n", "x", "i")) + 2000)
    kind.render = lambda item, state: TaskPrompt("parse/grouping-assign", "x" * 100000, item.key)
    decide(kind, CHARTER, conversations, paths.root, limit=1, **QUIET)
    [event] = [e for e in read_events(tmp_path / "log" / "events.jsonl") if e.event == "decision"]
    assert event.data["narrowedFrom"] > event.data["promptTokens"]


def test_the_prefilter_never_hides_a_group_whose_fact_is_unknown_or_assumed(scene):
    assert scene.shown(scene.kind.narrowed(scene.item, scene.knowledge)) == {"same", "unknown", "assumed", "none"}
    assert scene.shown(scene.kind.render(scene.item, scene.knowledge)) == {"same", "other", "unknown", "assumed", "none"}


def test_every_group_the_prefilter_hides_is_a_join_gate_c_refuses(scene):
    k = scene.kind
    hidden = scene.shown(k.render(scene.item, scene.knowledge)) - scene.shown(k.narrowed(scene.item, scene.knowledge))
    assert hidden == {"other"}
    for gid in hidden:
        decision, problems = k.check(scene.item, json.dumps(join(gid)), scene.knowledge)
        assert decision is None and problems


def test_an_item_with_no_signature_hides_nothing(scene):
    scene.kind.profiles[scene.item.id] = replace(scene.kind.profiles[scene.item.id], signature=None)
    assert len(scene.shown(scene.kind.narrowed(scene.item, scene.knowledge))) == 5


def test_still_over_after_the_prefilter_is_a_coded_stop_naming_size_and_role_with_nothing_asked(paths):
    conversations = scripted(by_name, 10)
    with pytest.raises(OverBudget) as e:
        decide(GroupingKind(paths, FAMILIES), CHARTER, conversations, paths.root, **QUIET)
    assert e.value.code == "over_budget" and "over_budget" in CODES
    assert KEY in str(e.value) and "is 10," in str(e.value) and "before the exact-fact prefilter" in str(e.value)
    assert conversations.started == 0 and not list((paths.root / "outbox").glob("*/0*.json"))


def test_a_raised_budget_resumes_where_the_stop_left_off(paths):
    with pytest.raises(OverBudget):
        decide(GroupingKind(paths, FAMILIES), CHARTER, scripted(by_name, 10), paths.root, **QUIET)
    knowledge = decide(GroupingKind(paths, FAMILIES), CHARTER, scripted(by_name, 100000), paths.root, **QUIET)
    assert knowledge.version == len(GroupingKind(paths, FAMILIES).pending())


def test_another_role_over_budget_stops_without_a_prefilter(paths):
    decide(GroupingKind(paths, FAMILIES), CHARTER, ScriptedConversations(by_name), paths.root, **QUIET)
    report(paths, FAMILIES)
    conversations = scripted(lambda *_: {"findings": []}, 10, "device.grouping.supervisor.budget")
    with pytest.raises(OverBudget) as e:
        review_cmd.review(paths, conversations, LIBRARY, **QUIET)
    assert "device.grouping.supervisor.budget is 10," in str(e.value) and "prefilter" not in str(e.value)
    assert conversations.started == 0


def test_a_direct_ask_is_checked_too():
    with pytest.raises(OverBudget):
        ask(scripted(by_name, 1), CHARTER, TaskPrompt("n", "x" * 100, "i"), lambda t: (None, []), Limits())


def spawned(settings):
    args = argparse.Namespace(agent="dry-run", auth=None, model=None, effort=None, agent_role=GROUPING_SUPERVISOR)
    return spawn(args, settings, ScriptedConversations(by_name))


def test_spawn_hands_the_engine_the_roles_budget_and_a_stop_is_one_coded_line(tmp_path, capsys):
    assert spawned(load(None, {}, {})).budget == Budget(GROUPING_SUPERVISOR.budget_row.key, GROUPING_SUPERVISOR.budget)
    config = tmp_path / "c.yaml"
    config.write_text("device: {grouping: {supervisor: {budget: 1}}}\n")
    conversations = spawned(load(config, {}, {}))
    assert reported(lambda: ask(conversations, CHARTER, TaskPrompt("n", "x", "i"), lambda t: (None, []), Limits())) == 1
    assert capsys.readouterr().err.splitlines()[-1].startswith(
        "error over_budget: device.grouping.supervisor.budget is 1, item i measures ")
