"""Every stage end to end on the fixture results: inbound → grouping (build, assign, report) → worthiness."""
import json
from pathlib import Path

import pytest
from helpers import QUIET

from perfrepair.data_handler.inbound.__main__ import main as inbound
from perfrepair.grouping.build.stage import build_stage
from perfrepair.grouping.kind import GroupingKind
from perfrepair.orchestrate.engine.decide import decide
from perfrepair.grouping.paths import GroupingPaths
from perfrepair.grouping.report.checks import report
from perfrepair.orchestrate.agent import ScriptedConversations
from perfrepair.orchestrate.commands.worthiness import worthiness
from perfrepair.result.modes import MODES
from perfrepair.validation import ValidationFailed
from perfrepair.validation.run import validate_run

F = Path(__file__).parent / "fixtures" / "results" / "manifest.yaml"


def same_name(message, *_):
    """Join the group whose example shares the item's name; otherwise found one."""
    item = message.split("ITEM\n  id ")[1].split(" · ")
    for line in message.splitlines():
        if line.startswith("      e.g. ") and f"{item[2]} @" in line:
            group = message.splitlines()[message.splitlines().index(line) - 1].split()[0]
            return {"group": group, "newGroup": {"id": "", "description": ""}, "amend": [], "reason": "same"}
    slug = "g-" + item[0]
    return {"group": "", "newGroup": {"id": slug, "description": f"the function {item[2]}"}, "amend": [], "reason": "new"}


def first_improving_pair(user, *_):
    lines = [line for line in user.splitlines() if " -> " in line and line.strip().endswith("True")]
    a, b = lines[0].split("|")[0].strip().split(" -> ")
    return {"decision": "test", "pairs": [{"from": a, "to": b, "reason": "faster outside spread"}], "reason": "clear gain"}


@pytest.fixture
def run(tmp_path):
    assert inbound(["--manifest", str(F), "-o", str(tmp_path)]) == 0
    build_stage(F, tmp_path)
    paths = GroupingPaths(tmp_path)
    decide(GroupingKind(paths), ScriptedConversations(same_name), paths.root, **QUIET)
    report(GroupingPaths(tmp_path))
    return tmp_path


def test_all_stages_validate(run):
    groups = json.loads(GroupingPaths(run).groups.read_text())
    shared = [g for g in groups["groups"] if len(g["members"]) == 2]
    assert len(shared) == 1
    latency = worthiness(run, MODES["latency"], ScriptedConversations(first_improving_pair), **QUIET)
    battery = worthiness(run, MODES["battery"], ScriptedConversations(first_improving_pair), **QUIET)
    assert [v.decision for v in latency.verdicts.values() if v.source == "llm"] == ["test"]
    assert {v.decision for v in battery.verdicts.values()} <= {"not_comparable", "no_improvement"}
    assert all(not problems for problems in validate_run(run).values())


def test_a_hand_edited_grouping_is_caught(run):
    path = GroupingPaths(run).groups
    doc = json.loads(path.read_text())
    doc["groups"][0]["members"].append(doc["groups"][1]["members"][0])
    path.write_text(json.dumps(doc))
    assert validate_run(run)["grouping/groups.json"]
    with pytest.raises(ValidationFailed):
        worthiness(run, MODES["latency"], ScriptedConversations(first_improving_pair), **QUIET)
