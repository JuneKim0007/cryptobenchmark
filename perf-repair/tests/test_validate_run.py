import json

from test_stages import run  # noqa: F401  (the stage fixture)

from perfrepair.grouping.paths import GroupingPaths
from perfrepair.validation.run import validate_run


def test_a_hand_edited_knowledge_is_caught(run):
    path = GroupingPaths(run).knowledge
    doc = json.loads(path.read_text())
    doc["dropped"].append(999)
    path.write_text(json.dumps(doc))
    assert validate_run(run)["grouping"]


def test_an_active_switched_to_an_older_outbox_is_caught(run):
    root = GroupingPaths(run).root / "outbox"
    current = (root / "active").read_text().strip()
    older = root / "0123456789ab"
    older.mkdir()
    (older / "000001.json").write_bytes((root / current / "000001.json").read_bytes())
    (root / "active").write_text("0123456789ab\n")
    assert any("records committed" in p for p in validate_run(run)["grouping"])


def test_a_broken_active_is_reported_not_raised(run):
    (GroupingPaths(run).root / "outbox" / "active").write_text("../elsewhere\n")
    assert any("outbox_active_invalid" in p for p in validate_run(run)["grouping"])
