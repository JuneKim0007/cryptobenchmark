"""Records name items by Item.key, so ids moving and items leaving replay correctly."""
import json
from dataclasses import replace

import pytest
from conftest import LIBRARY, QUIET, by_name
from grouping_data import FAMILIES

from perfrepair.ai.parse.grouping_assign.kind import GroupingKind, charter
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.runtime.engine.decide import decide
from perfrepair.ai.runtime.engine.outbox import active_fingerprint, active_outbox
from cryptobench.catalogue.grouping import Item, items_document, read_items, read_profiles, profiles_document
from perfrepair.files import read_json, write_json
from perfrepair.grouping.report.checks import report
from perfrepair.validation.parse.grouping_assign import validate_answer
from perfrepair.dto.grouping_state import Answer


def assign(paths, agent=None):
    agent = agent or ScriptedConversations(by_name)
    kind = GroupingKind(paths, FAMILIES)
    return decide(kind, charter(LIBRARY), agent, paths.root, **QUIET), agent


def renumber(paths, keep=lambda _: True):
    """items.json and profiles.json as a rebuild leaves them: the kept items numbered from 1."""
    items, profiles = read_items(read_json(paths.items)), read_profiles(read_json(paths.profiles))
    kept = [i for i in items if keep(i)]
    moved = [replace(i, id=n) for n, i in enumerate(kept, 1)]
    write_json(paths.items, items_document(moved))
    write_json(paths.profiles, profiles_document({m.id: profiles[i.id] for m, i in zip(moved, kept)}))


def members(knowledge, items):
    return sorted(sorted(items[m].qualified for m in g.members) for g in knowledge.groups.values())


def test_ids_moving_keep_each_answer_on_its_own_item_and_ask_nothing(paths):
    before, _ = assign(paths)
    first = GroupingKind(paths, FAMILIES).items()[0]
    names = [[q for q in group if q != first.qualified] for group in members(before, GroupingKind(paths, FAMILIES).by_id)]
    renumber(paths, keep=lambda i: i != first)
    assert GroupingKind(paths, FAMILIES).by_id[1].qualified != first.qualified
    after, agent = assign(paths)
    assert agent.started == 0 and members(after, GroupingKind(paths, FAMILIES).by_id) == [g for g in names if g]


def test_an_item_that_left_is_in_no_group_and_a_group_it_alone_held_is_gone(paths):
    assign(paths)
    renumber(paths, keep=lambda i: i.name != "H1")
    knowledge, agent = assign(paths)
    assert agent.started == 0 and "h1" not in knowledge.groups and "h1" in knowledge.retired
    document = report(paths, FAMILIES)
    assert not [q for q in document["items"].values() if "H1" in q["qualified"]]
    assert "h1" not in {g["id"] for g in document["groups"]} and "h1" not in json.dumps(read_json(paths.knowledge)["groups"])


def test_a_group_whose_creator_left_keeps_its_other_members(paths):
    first, _ = assign(paths)
    kind = GroupingKind(paths, FAMILIES)
    gid, group = next((g, v) for g, v in first.groups.items() if len(v.members) > 1)
    creator = kind.by_id[group.members[0]]
    survivor = kind.by_id[group.members[1]]
    renumber(paths, keep=lambda i: i != creator)
    knowledge, agent = assign(paths)
    assert agent.started == 0 and gid in knowledge.groups
    assert [GroupingKind(paths, FAMILIES).by_id[m].qualified for m in knowledge.groups[gid].members] == [survivor.qualified]


def test_an_answer_cannot_reuse_the_id_of_a_group_that_left(paths):
    assign(paths)
    renumber(paths, keep=lambda i: i.name != "H1")
    knowledge, _ = assign(paths)
    item = GroupingKind(paths, FAMILIES).items()[0]
    answer = Answer(newGroupId="h1", newGroupDescription="again", reason="r")
    assert any("already exists" in p for p in validate_answer(answer, item, knowledge, FAMILIES))


def test_an_item_that_comes_back_returns_to_its_group_with_no_call(paths):
    before, _ = assign(paths)
    full = read_json(paths.items), read_json(paths.profiles)
    renumber(paths, keep=lambda i: i.name != "H1")
    assign(paths)
    write_json(paths.items, full[0])
    write_json(paths.profiles, full[1])
    again, agent = assign(paths)
    assert agent.started == 0 and again.to_json()["groups"] == before.to_json()["groups"]


def test_a_new_family_for_a_name_is_a_new_question(paths):
    assign(paths)
    doc = read_json(paths.items)
    target = doc["items"][0]
    target["family"] = "unidentified"
    write_json(paths.items, doc)
    profiles = read_profiles(read_json(paths.profiles))
    write_json(paths.profiles, profiles_document({**profiles, target["id"]: replace(profiles[target["id"]], keyKind="unknown")}))
    before = len(active_outbox(paths.root).records())
    assign(paths)
    last = active_outbox(paths.root).records()[before:]
    assert [r.item.split("|")[0] for r in last] == ["unidentified"]


def test_replay_of_a_numeric_record_is_a_coded_error():
    with pytest.raises(ValueError, match="^outbox_unkeyed: "):
        Item.from_key("3")

