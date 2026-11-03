"""Records name items by Item.key, so ids moving, items leaving and old positional outboxes all replay correctly."""
import json
from dataclasses import replace

import pytest
from conftest import LIBRARY, QUIET, by_name
from grouping_data import FAMILIES

from perfrepair.ai.parse.grouping_assign.kind import GroupingKind, charter, refresh_inputs
from perfrepair.ai.parse.grouping_assign.rekey import rekey
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.runtime.engine.decide import decide
from perfrepair.ai.runtime.engine.kind import project
from perfrepair.ai.runtime.engine.outbox import activate, active_fingerprint, active_outbox
from perfrepair.dto.grouping import Item, items_document, read_items, read_profiles, profiles_document
from perfrepair.files import read_json, write_json
from perfrepair.grouping.report.checks import report
from perfrepair.screen.groups import screened_out
from perfrepair.validation.parse.grouping_assign import validate_answer
from perfrepair.dto.grouping_state import Answer


def assign(paths, agent=None):
    agent = agent or ScriptedConversations(by_name)
    kind = GroupingKind(paths, FAMILIES)
    return decide(kind, charter(LIBRARY, kind.inputs), agent, paths.root, **QUIET), agent


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
    target["family"] = "cipher.unknown"
    write_json(paths.items, doc)
    profiles = read_profiles(read_json(paths.profiles))
    write_json(paths.profiles, profiles_document({**profiles, target["id"]: replace(profiles[target["id"]], keyKind="unknown")}))
    before = len(active_outbox(paths.root).records())
    assign(paths)
    last = active_outbox(paths.root).records()[before:]
    assert [r.item.split("|")[0] for r in last] == ["cipher.unknown"]


def test_replay_of_a_numeric_record_is_a_coded_error():
    with pytest.raises(ValueError, match="^outbox_unkeyed: "):
        Item.from_key("3")


def test_refresh_asks_every_item_into_a_new_outbox_and_later_runs_stay_in_it(paths):
    _, agent = assign(paths)
    old = active_fingerprint(paths.root)
    kind = GroupingKind(paths, FAMILIES)
    fresh = ScriptedConversations(by_name)
    decide(kind, charter(LIBRARY, refresh_inputs()), fresh, paths.root, **QUIET)
    new = active_fingerprint(paths.root)
    assert new != old and fresh.started == agent.started and (paths.root / "outbox" / old).is_dir()
    assert GroupingKind(paths, FAMILIES).inputs.startswith("refresh ")
    _, again = assign(paths)
    assert again.started == 0 and active_fingerprint(paths.root) == new


def _positional_outbox(paths, kind):
    """The folder as the engine left it when records named positions and the inputs were the screened-out ids."""
    inputs = "\n".join(str(k) for k, v in sorted((kind.screen or {}).items()) if screened_out(v))
    assign(paths)
    decided = active_outbox(paths.root).records()
    old = charter(LIBRARY, inputs)
    if old.fingerprint == active_fingerprint(paths.root):
        return old, decided
    outbox, _ = activate(paths.root, old)
    for r in decided:
        item = next(i for i in kind.items() if i.key == r.item)
        outbox.append(replace(r, item=str(item.id)))
    return old, decided


def test_a_positional_outbox_moves_to_keys_with_no_call_and_stays_behind(paths):
    from helpers import CATALOG
    from perfrepair.dto.screen import Verdict, screen_document
    from perfrepair.run_dir import built
    verdicts = {n: Verdict("broken", "r", "s", "H1") if n == 6 else Verdict("accepted", "r", "s", f"A{n}") for n in range(1, 7)}
    write_json(paths.screen, screen_document(verdicts, CATALOG, built(paths)))
    old, decided = _positional_outbox(paths, GroupingKind(paths, FAMILIES))
    assert rekey(paths, LIBRARY) is True
    assert [r.item for r in active_outbox(paths.root).records()] == [r.item for r in decided]
    assert (paths.root / "outbox" / old.fingerprint / "000001.json").is_file()
    assert active_fingerprint(paths.root) != old.fingerprint and rekey(paths, LIBRARY) is False
    kind = GroupingKind(paths, FAMILIES)
    assert project(kind, active_outbox(paths.root).records()).version == len(decided)


def test_a_positional_outbox_whose_positions_moved_is_left_and_asked(paths, caplog):
    from helpers import CATALOG
    from perfrepair.dto.screen import Verdict, screen_document
    from perfrepair.run_dir import built
    verdicts = {n: Verdict("broken", "r", "s", "H1") if n == 6 else Verdict("accepted", "r", "s", f"A{n}") for n in range(1, 7)}
    write_json(paths.screen, screen_document(verdicts, CATALOG, built(paths)))
    old, decided = _positional_outbox(paths, GroupingKind(paths, FAMILIES))
    verdicts[6], verdicts[5] = verdicts[5], verdicts[6]
    write_json(paths.screen, screen_document(verdicts, CATALOG, built(paths)))
    assert rekey(paths, LIBRARY) is False and "outbox_not_rekeyed" in caplog.text
    assert active_fingerprint(paths.root) == old.fingerprint
