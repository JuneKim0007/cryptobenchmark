"""tools/role_checks.py on the scripted gateway: its checks, report and cost, with no model."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml
from helpers import LATENCY, LIBRARY
from role_runs import ROLES, assigned_device, built_device
from site_replace_data import APP as REPLACE_APP
from test_upgrade import APP as UPGRADE_APP

from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.run_dir import GroupingPaths
from perfrepair.validation.screen import read_checked_screen

TOOL = Path(__file__).parents[1] / "tools" / "role_checks.py"
spec = importlib.util.spec_from_file_location("role_checks", TOOL)
role_checks = importlib.util.module_from_spec(spec)
sys.modules["role_checks"] = role_checks
spec.loader.exec_module(role_checks)
BY_NAME = {r.name: r for r in ROLES}


@pytest.fixture(autouse=True)
def every_item_asked(asked_by_model):
    yield


@pytest.fixture
def device(tmp_path):
    return assigned_device(built_device(tmp_path / "built"), tmp_path / "assigned")


def context(app=UPGRADE_APP):
    return role_checks.Context(LIBRARY, app, LATENCY.name)


def test_it_runs_every_role_but_classify_without_batches(device, tmp_path):
    report = role_checks.check_all(device, tmp_path / "out", [REPLACE_APP], 1, LATENCY.name, {},
                                   lambda role: ScriptedConversations(BY_NAME[role].right), LIBRARY)
    assert {r["role"] for r in report["rows"]} == set(role_checks.RUNNERS) - {"screening.classify"}
    assert report["pass"] and all(r["checks"]["identical rerun makes no call"] for r in report["rows"])
    assert all(r["checks"]["required input removed refuses before any call"] for r in report["rows"])


def _upgrade_on(device, tmp_path, answer, plan):
    return role_checks.check_role("repair-upgrade", device, tmp_path / "work", lambda: ScriptedConversations(answer),
                                  context(), plan)


FLIP = {"flips": {"repair-upgrade": [{"name": "site", "file": "{app}/dossiers.json", "old": '"return"', "new": '"local"'}]}}


def test_a_flip_the_answer_ignores_fails_and_one_it_follows_passes(device, tmp_path):
    ignores = _upgrade_on(device, tmp_path, lambda *_: {"option": "R1", "reason": "r"}, FLIP)
    follows = _upgrade_on(device, tmp_path, lambda task, *_: {"option": "R2" if "sinks: local" in task.text else "R1", "reason": "r"}, FLIP)
    assert ignores["checks"]["flip site changes the answer"] is False and not ignores["pass"]
    assert follows["checks"]["flip site changes the answer"] is True


def test_a_flip_of_text_the_file_lacks_is_an_error_not_a_pass(device, tmp_path):
    plan = {"flips": {"repair-upgrade": [{"name": "x", "file": "{app}/dossiers.json", "old": "absent", "new": "y"}]}}
    with pytest.raises(ValueError, match="flip x"):
        _upgrade_on(device, tmp_path, lambda *_: {"option": "R1", "reason": "r"}, plan)


def test_known_answers_give_a_match_rate_and_tokens_and_cost_are_summed(device, tmp_path):
    found = _upgrade_on(device, tmp_path, lambda *_: {"option": "R1", "reason": "r"}, {})
    assert found["usage"]["calls"] == 1 and found["usage"]["costUsd"] == 0 and found["usage"]["promptTokens"][0] > 0
    assert found["knownAnswers"] == {"known": 0, "asked": 0, "matched": 0, "rate": None}
    assert role_checks._matches({"a": {"option": "R1"}, "b": {"option": "R1"}, "c": {"option": "R1"}},
                                {"a": {"option": "R1"}, "b": {"option": "R2"}}) == {"known": 3, "asked": 2, "matched": 1, "rate": 0.5}


def test_the_source_folder_is_never_changed(device, tmp_path):
    before = sorted(p.name for p in device.rglob("*"))
    _upgrade_on(device, tmp_path, lambda *_: {"option": "R1", "reason": "r"}, FLIP)
    assert sorted(p.name for p in device.rglob("*")) == before


def test_a_flip_of_the_profiles_still_passes_the_screen_gate(device):
    flip = {"name": "x", "file": "grouping/profiles.json", "old": "true", "new": "true "}
    role_checks._flipped(device, flip, context())
    assert read_checked_screen(GroupingPaths(device)) is not None


def test_the_plan_example_parses():
    plan = yaml.safe_load((TOOL.parent / "role-checks.example.yaml").read_text())
    assert set(plan["flips"]) <= set(role_checks.RUNNERS) and json.dumps(plan)
