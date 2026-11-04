import json

import pytest
import yaml
from grouping_data import FAMILIES
from conftest import CHARTER, QUIET, by_name

from perfrepair.ai.parse.grouping_assign.kind import GroupingKind
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.runtime.engine.decide import decide
from perfrepair.dto.interop import failed_pairs, member, pair_status
from perfrepair.grouping.interop_plan import write_plan
from perfrepair.grouping.interop_read import import_results
from perfrepair.grouping.report.checks import report
from perfrepair.validation import ValidationFailed
from perfrepair.validation.grouping.interop import validate_interop, validate_plan

DIRECTIONS = {"pass": ("pass", "pass"), "fail": ("fail", "pass"), "not_checkable": ("not_checkable", "pass")}


@pytest.fixture
def grouped(paths):
    decide(GroupingKind(paths, FAMILIES), CHARTER, ScriptedConversations(by_name), paths.root, **QUIET)
    return paths, report(paths, FAMILIES)


def interop_yaml(plan, results, tmp_path):
    """What cryptobenchmark's InteropFile writes for the plan, one result per pair."""
    rows = []
    for pair, result in zip(plan, results):
        a, b = DIRECTIONS[result]
        rows.append({"id": pair.id, "group": pair.group, "a": member(pair.a), "b": member(pair.b), "result": result,
                     "mode": "produce_consume", "directions": {"aToB": a, "bToA": b},
                     "reason": "" if result == "pass" else f"aToB: {result} reason"})
    path = tmp_path / "interop.yaml"
    path.write_text(yaml.safe_dump({"schemaVersion": 1, "generatedFrom": {"plan": "p", "capture": "c"}, "pairs": rows}))
    return path


def test_the_plan_pairs_every_two_runnable_members_once(grouped):
    paths, groups = grouped
    plan = write_plan(paths)
    expected = sum(len(g["runnable"]) * (len(g["runnable"]) - 1) // 2 for g in groups["groups"])
    assert len(plan) == expected > 0
    assert [p.id for p in plan] == list(range(1, expected + 1))
    written = yaml.safe_load(paths.interop_plan.read_text())
    assert written["schemaVersion"] == 1 and set(written["pairs"][0]["a"]) == {"type", "algorithm", "provider"}
    assert validate_plan(written, groups) == []


def test_groups_start_not_run(grouped):
    _, groups = grouped
    assert groups["interop"] == {"status": "not_run", "pairs": []}
    assert failed_pairs(groups) == set()


@pytest.mark.parametrize("result,kind,severity", [("fail", "interop_failed", "error"),
                                                    ("not_checkable", "interop_not_checkable", "info")])
def test_reading_results_records_findings_and_marks_pairs(grouped, tmp_path, result, kind, severity):
    paths, _ = grouped
    plan = write_plan(paths)
    import_results(paths, interop_yaml(plan, [result] * len(plan), tmp_path))
    groups = report(paths, FAMILIES)
    assert groups["interop"]["status"] == "checked"
    assert failed_pairs(groups) == ({frozenset((p.a, p.b)) for p in plan} if result == "fail" else set())
    assert pair_status(groups, plan[0].b, plan[0].a) == result
    findings = json.loads(paths.checks.read_text())["findings"]
    assert {(f["kind"], f["severity"], f["group"]) for f in findings if f["kind"].startswith("interop")} == {
        (kind, severity, p.group) for p in plan}
    assert kind in next(g for g in groups["groups"] if g["id"] == plan[0].group)["findings"]
    assert all(v == [] for v in validate_interop(groups, paths.interop_plan, paths.interop).values())


def test_results_that_do_not_answer_the_plan_are_refused(grouped, tmp_path):
    paths, _ = grouped
    plan = write_plan(paths)
    source = interop_yaml(plan, ["pass"] * len(plan), tmp_path)
    doc = yaml.safe_load(source.read_text())
    doc["pairs"][0]["b"]["provider"] = "Elsewhere"
    doc["pairs"][0]["result"] = "fail"
    doc["pairs"].append({**doc["pairs"][0], "id": 99})
    source.write_text(yaml.safe_dump(doc))
    with pytest.raises(ValidationFailed) as e:
        import_results(paths, source)
    text = str(e.value.problems)
    assert "not the plan's" in text and "is not the planned" in text and "disagrees with directions" in text
    assert not paths.interop.exists()


def test_results_need_their_plan(grouped, tmp_path):
    paths, _ = grouped
    with pytest.raises(ValidationFailed, match="run interop-plan"):
        import_results(paths, tmp_path / "interop.yaml")


def test_a_stale_groups_section_is_a_problem(grouped, tmp_path):
    paths, groups = grouped
    plan = write_plan(paths)
    import_results(paths, interop_yaml(plan, ["fail"] * len(plan), tmp_path))
    problems = validate_interop(groups, paths.interop_plan, paths.interop)
    assert problems["grouping/groups.json interop"] == [
        "groups.json interop section differs from grouping/interop.yaml; rerun grouping report"]
