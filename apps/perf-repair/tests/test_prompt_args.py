from pathlib import Path

import pytest

from perfrepair.ai.parse.grouping_assign.kind import charter as assign_charter
from perfrepair.ai.runtime.engine.outbox import active_fingerprint
from perfrepair.ai.runtime.prompt import PromptLibrary
from perfrepair.data_handler.inbound.__main__ import main as inbound
from perfrepair.grouping.__main__ import main as grouping
from perfrepair.run_dir import GroupingPaths
from helpers import with_results

F = Path(__file__).parent / "fixtures" / "results" / "test-api36-00000000" / "manifest.yaml"
DRY = ["--agent", "dry-run"]


@pytest.fixture
def run(tmp_path):
    run = tmp_path / "run"
    assert inbound(["--device-results", str(with_results(run))]) == 0
    assert grouping(["build", "--device-results", str(with_results(run))]) == 0
    return run


def overriding(tmp_path, relative, extra):
    folder = tmp_path / "prompts"
    (folder / relative).parent.mkdir(parents=True)
    (folder / relative).write_text((PromptLibrary.load().source(relative.removesuffix(".system.md"))).read_text() + extra)
    return folder


def outboxes(root):
    return sorted(p.name for p in (root / "outbox").iterdir() if p.is_dir())


def test_a_typo_file_exits_2_before_any_work(run, tmp_path, capsys):
    typo = tmp_path / "typo"
    (typo / "parse").mkdir(parents=True)
    (typo / "parse" / "grouping-asign.system.md").write_text("x")
    with pytest.raises(SystemExit) as exit_:
        grouping(["assign", "--device-results", str(run), *DRY, "--prompts", str(typo)])
    assert exit_.value.code == 2
    assert "error: prompt_unknown" in capsys.readouterr().err
    assert sorted(p.name for p in GroupingPaths(run).root.iterdir()) == ["items.json", "profiles.json", "screen.json"]


def test_assign_with_an_override_decides_into_a_new_outbox_beside_the_default(run, tmp_path):
    root = GroupingPaths(run).root
    assert grouping(["assign", "--device-results", str(run), *DRY]) == 0
    default = active_fingerprint(root)
    assert default == assign_charter(PromptLibrary.load()).fingerprint
    folder = overriding(tmp_path, "parse/grouping-assign.system.md", "\nOVERRIDE")
    assert grouping(["assign", "--device-results", str(run), *DRY, "--prompts", str(folder)]) == 0
    overridden = active_fingerprint(root)
    assert overridden == assign_charter(PromptLibrary.load(folder)).fingerprint != default
    assert outboxes(root) == sorted([default, overridden])


