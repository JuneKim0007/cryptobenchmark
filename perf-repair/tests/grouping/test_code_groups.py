import json

import pytest
from conftest import LIBRARY, QUIET, by_name
from grouping_data import FAMILIES

from perfrepair.ai.parse.grouping_assign.kind import GroupingKind, charter
from perfrepair.ai.review.grouping_review.run import charter as supervisor_charter, supervise
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.runtime.engine.decide import decide
from perfrepair.ai.runtime.engine.outbox import active_fingerprint, active_outbox
from perfrepair.dto.grouping_state import Group, code_made
from helpers import CATALOG
from perfrepair.dto.screen import Verdict, screen_document
from perfrepair.files import write_json
from perfrepair.run_dir import built
from perfrepair.grouping.interop_plan import plan
from perfrepair.grouping.report.checks import report
from perfrepair.validation import ValidationFailed
from perfrepair.validation.grouping.output import read_groups, validate_output
from perfrepair.validation.parse.grouping_assign import SLUG

BROKEN = {3: "ALG-S/M1", 4: "ALG-S/M1", 6: "H1"}


def screen(paths, broken=BROKEN):
    verdicts = {n: Verdict("broken", "r", "s", broken[n]) if n in broken else Verdict("accepted", "r", "s", f"A{n}")
                for n in range(1, 7)}
    write_json(paths.screen, screen_document(verdicts, CATALOG, built(paths)))


def assign(paths):
    kind = GroupingKind(paths, FAMILIES)
    agent = ScriptedConversations(by_name)
    return decide(kind, charter(LIBRARY, kind.inputs), agent, paths.root, **QUIET), agent


def code_groups_of(knowledge):
    return {gid: g.members for gid, g in knowledge.groups.items() if code_made(gid)}


def test_without_screen_json_every_item_is_asked(paths):
    kind = GroupingKind(paths, FAMILIES)
    assert kind.pending() == kind.items() and kind.inputs == "" and kind.empty().groups == {}


def test_broken_items_are_grouped_by_code_per_canonical_key_and_never_asked(paths):
    screen(paths)
    knowledge, agent = assign(paths)
    assert agent.started == 3 and {r.item for r in active_outbox(paths.root).records()} == {"1", "2", "5"}
    assert sorted(code_groups_of(knowledge).values()) == [[3, 4], [6]]
    assert all(not SLUG.match(gid) for gid in code_groups_of(knowledge))
    assert json.loads(paths.cursor.read_text())["next"] is None


def test_a_code_group_id_is_a_digest_of_its_key_not_of_the_run(paths):
    screen(paths)
    assert code_groups_of(GroupingKind(paths, FAMILIES).empty())["code_3833fa2f64"] == [6]


def test_groups_json_carries_code_groups_and_each_items_screen(paths):
    screen(paths)
    assign(paths)
    document = report(paths, FAMILIES)
    assert {k: e["screen"] for k, e in document["items"].items()}["3"] == "broken"
    coded = [g for g in document["groups"] if code_made(g["id"])]
    assert sorted(g["members"] for g in coded) == [[3, 4], [6]]
    assert all(g["description"].startswith("Code-made group of one algorithm") for g in coded)
    assert [p.group for p in plan(read_groups(paths))].count(next(g["id"] for g in coded if g["members"] == [3, 4])) == 1


def test_the_supervisor_reviews_model_groups_only(paths):
    screen(paths)
    assign(paths)
    report(paths, FAMILIES)
    used = supervisor_charter(LIBRARY)
    seen = []
    supervise(paths, used, ScriptedConversations(lambda m, *_: seen.append(m.text) or {"findings": []}),
              LIBRARY.provenance(used), **QUIET)
    assert len(seen) == 3 and not any("code_" in text or "FAMILY digest.none" in text for text in seen)


def test_an_answer_may_not_join_or_amend_a_code_made_group(paths):
    screen(paths, {4: "ALG-S/M1"})
    kind = GroupingKind(paths, FAMILIES)
    knowledge = kind.empty()
    gid = next(iter(code_groups_of(knowledge)))
    join = json.dumps({"group": gid, "newGroup": {"id": "", "description": ""}, "amend": [], "reason": "same"})
    amend = json.dumps({"group": "", "newGroup": {"id": "s", "description": "d" * 3}, "reason": "x",
                        "amend": [{"group": gid, "description": "changed"}]})
    assert "is not a group of family" in kind.check(kind.by_id[3], join, knowledge)[1][0]
    assert any("not a group of family" in p for p in kind.check(kind.by_id[3], amend, knowledge)[1])
    assert gid not in kind.render(kind.by_id[3], knowledge).text


def test_a_screen_change_after_assign_rotates_the_outbox_and_reverting_resumes(paths):
    screen(paths, {})
    before, _ = assign(paths)
    old = active_fingerprint(paths.root)
    screen(paths, {6: "H1"})
    with pytest.raises(ValidationFailed, match="item 6 is grouped by code"):
        report(paths, FAMILIES)
    after, agent = assign(paths)
    assert active_fingerprint(paths.root) != old and agent.started == 5
    assert list(code_groups_of(after).values()) == [[6]]
    report(paths, FAMILIES)
    screen(paths, {})
    reverted, agent = assign(paths)
    assert active_fingerprint(paths.root) == old and agent.started == 0
    assert reverted.to_json() == before.to_json()


def test_validate_output_holds_broken_items_to_their_code_groups(paths):
    screen(paths)
    assign(paths)
    document = report(paths, FAMILIES)
    kind = GroupingKind(paths, FAMILIES)
    gid = next(g["id"] for g in document["groups"] if g["members"] == [6])
    moved = json.loads(json.dumps(document))
    model = next(g for g in moved["groups"] if not code_made(g["id"]))
    moved["groups"] = [g for g in moved["groups"] if g["id"] != gid]
    model["members"].append(6)
    moved["items"]["6"]["group"] = model["id"]
    moved["items"]["1"]["screen"] = "unknown"
    problems = validate_output(moved, kind.by_id, kind.screen)
    assert f"item 6: screened broken, but in model group {model['id']}; rerun assign" in problems
    assert f"group {gid}: code-made group missing" in problems
    assert "item 1: screen 'unknown', screen.json says 'accepted'" in problems
    assert validate_output(document, kind.by_id, kind.screen) == []


def test_a_code_made_group_must_be_the_one_screen_json_implies(paths):
    screen(paths)
    kind = GroupingKind(paths, FAMILIES)
    knowledge = kind.empty()
    gid = next(g for g, m in code_groups_of(knowledge).items() if m == [3, 4])
    knowledge.groups[gid].members.remove(4)
    knowledge.groups["code_0000000000"] = Group("cipher.secret", "x", [4])
    problems = kind.validate(knowledge, [])
    assert any(p.startswith(f"group {gid}: differs from the code-made group") for p in problems)
    assert "group code_0000000000: code-made, but screen.json makes no such group" in problems


def test_a_status_change_that_asks_the_same_items_keeps_the_outbox(paths):
    screen(paths)
    assign(paths)
    old = active_fingerprint(paths.root)
    verdicts = {n: Verdict("broken", "r", "s", BROKEN[n]) if n in BROKEN else Verdict("unknown", "other reason", None, f"A{n}")
                for n in range(1, 7)}
    write_json(paths.screen, screen_document(verdicts, CATALOG, built(paths)))
    _, agent = assign(paths)
    assert active_fingerprint(paths.root) == old and agent.started == 0
