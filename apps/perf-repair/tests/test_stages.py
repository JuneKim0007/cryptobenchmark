import json
from pathlib import Path

import pytest
import yaml
from helpers import with_results, LIBRARY, QUIET

from perfrepair.data_handler.inbound.__main__ import main as inbound
from perfrepair.grouping.build.stage import build_stage
from perfrepair.ai.parse.grouping_assign.kind import GroupingKind, charter
from perfrepair.ai.runtime.engine.decide import decide
from perfrepair.ai.runtime.engine.outbox import active_fingerprint
from perfrepair.grouping.__main__ import main as grouping_main
from perfrepair.run_dir import GroupingPaths
from perfrepair.grouping.report.checks import report
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.evaluate.worthiness.command import worthiness
from helpers import LATENCY, LATENCY_ALLOC
from perfrepair.validation import ValidationFailed
from perfrepair.check.run import validate_run
from perfrepair.screen.catalog import screening_catalog

F = Path(__file__).parent / "fixtures" / "results" / "test-api36-00000000" / "manifest.yaml"


def same_name(task, *_):
    message = yaml.safe_load(task.text)
    item = message["item"]
    for group in message["groups"]:
        if any(m.startswith(f"{item['name']} @") for m in group["members"]):
            return {"group": group["id"], "newGroup": {"id": "", "description": ""}, "amend": [], "reason": "same"}
    slug = f"g-{item['id']}"
    return {"group": "", "newGroup": {"id": slug, "description": f"the function {item['name']}"}, "amend": [], "reason": "new"}


def first_improving_pair(task, *_):
    lines = [line for line in task.text.splitlines() if " -> " in line and line.strip().endswith("True")]
    a, b = lines[0].split("|")[0].strip().split(" -> ")
    return {"decision": "test", "pairs": [{"from": a, "to": b, "reason": "faster outside spread"}], "reason": "clear gain"}


@pytest.fixture
def run(tmp_path):
    assert inbound(["--device-results", str(with_results(tmp_path))]) == 0
    build_stage(F, tmp_path, screening_catalog(None))
    paths = GroupingPaths(tmp_path)
    decide(GroupingKind(paths), charter(LIBRARY), ScriptedConversations(same_name), paths.root, **QUIET)
    report(GroupingPaths(tmp_path))
    return tmp_path


def test_all_stages_validate(run):
    groups = json.loads(GroupingPaths(run).groups.read_text())
    shared = [g for g in groups["groups"] if len(g["members"]) == 2]
    assert len(shared) == 1
    latency = worthiness(run, LATENCY, ScriptedConversations(first_improving_pair), LIBRARY, **QUIET)
    alloc = worthiness(run, LATENCY_ALLOC, ScriptedConversations(first_improving_pair), LIBRARY, **QUIET)
    assert [v.decision for v in latency.verdicts.values() if v.source == "llm"] == ["test"]
    assert {v.decision for v in alloc.verdicts.values()} == {"not_comparable", "not_measured"}
    assert all(not problems for problems in validate_run(run, screening_catalog(None)).values())


def test_changing_the_effort_keeps_the_assign_outbox(run):
    root = GroupingPaths(run).root
    assert grouping_main(["assign", "--device-results", str(run), "--agent", "dry-run", "--effort", "low"]) == 0
    before = active_fingerprint(root)
    assert grouping_main(["assign", "--device-results", str(run), "--agent", "dry-run", "--effort", "max"]) == 0
    assert active_fingerprint(root) == before


def test_a_hand_edited_grouping_is_caught(run):
    path = GroupingPaths(run).groups
    doc = json.loads(path.read_text())
    doc["groups"][0]["members"].append(doc["groups"][1]["members"][0])
    path.write_text(json.dumps(doc))
    assert validate_run(run, screening_catalog(None))["grouping/groups.json"]
    with pytest.raises(ValidationFailed):
        worthiness(run, LATENCY, ScriptedConversations(first_improving_pair), LIBRARY, **QUIET)


def test_a_run_without_rows_is_a_reported_problem(tmp_path):
    from perfrepair.validation.__main__ import main
    assert validate_run(tmp_path, screening_catalog(None)) == {"rows.json": [f"missing: {tmp_path / 'rows.json'}"]}
    assert main(["--device-results", str(tmp_path)]) == 1
