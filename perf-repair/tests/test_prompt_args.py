import json
from pathlib import Path

import pytest

from perfrepair.ai.__main__ import main as ai
from perfrepair.ai.review.grouping_review.run import charter as supervisor_charter
from perfrepair.ai.runtime.prompt import PromptLibrary
from perfrepair.data_handler.inbound.__main__ import main as inbound
from perfrepair.grouping.__main__ import main as grouping
from perfrepair.grouping.paths import GroupingPaths

F = Path(__file__).parent / "fixtures" / "results" / "manifest.yaml"
DRY = ["--agent", "dry-run"]


@pytest.fixture
def run(tmp_path):
    run = tmp_path / "run"
    assert inbound(["--manifest", str(F), "-o", str(run)]) == 0
    assert grouping(["build", "--manifest", str(F), "--run", str(run)]) == 0
    return run


@pytest.fixture
def override(tmp_path):
    folder = tmp_path / "prompts"
    (folder / "review").mkdir(parents=True)
    (folder / "review" / "grouping-review.system.md").write_text("REVIEW OVERRIDE")
    return folder


def supervised(run, *extra):
    assert grouping(["assign", "--run", str(run), *DRY, *extra]) == 0
    assert grouping(["report", "--run", str(run), "--supervisor", *DRY, *extra]) == 0
    return json.loads(GroupingPaths(run).supervisor.read_text())


def test_no_flag_uses_the_packaged_prompts(run):
    library = PromptLibrary.load()
    doc = supervised(run)
    assert doc["charter"] == supervisor_charter(library).fingerprint
    assert doc["prompts"]["review/grouping-review"] == str(library.source("review/grouping-review"))


def test_an_override_folder_is_used_and_recorded(run, override):
    doc = supervised(run, "--prompts", str(override))
    assert doc["charter"] == supervisor_charter(PromptLibrary.load(override)).fingerprint
    assert doc["charter"] != supervisor_charter(PromptLibrary.load()).fingerprint
    assert doc["prompts"]["review/grouping-review"] == str(override / "review" / "grouping-review.system.md")


@pytest.mark.parametrize("command", [["assign"], ["report", "--supervisor"]])
def test_a_typo_file_exits_2_before_any_work(run, tmp_path, capsys, command):
    typo = tmp_path / "typo"
    (typo / "review").mkdir(parents=True)
    (typo / "review" / "grouping-reveiw.system.md").write_text("x")
    with pytest.raises(SystemExit) as exit_:
        grouping([*command, "--run", str(run), *DRY, "--prompts", str(typo)])
    assert exit_.value.code == 2
    assert "error: prompt_unknown" in capsys.readouterr().err
    assert sorted(p.name for p in GroupingPaths(run).root.iterdir()) == ["items.json", "profiles.json"]


def test_worthiness_rejects_a_missing_prompts_folder(run, tmp_path, capsys):
    with pytest.raises(SystemExit) as exit_:
        ai(["worthiness", "--run", str(run), "--mode", "latency", *DRY, "--prompts", str(tmp_path / "absent")])
    assert exit_.value.code == 2
    assert "error: missing_directory" in capsys.readouterr().err
