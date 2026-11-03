import pytest
import json

from test_stages import run  # noqa: F401  (the stage fixture)

from perfrepair.run_dir import GroupingPaths
from perfrepair.check.run import validate_run
from perfrepair.screen.catalog import screening_catalog


def test_a_hand_edited_knowledge_is_caught(run):
    path = GroupingPaths(run).knowledge
    doc = json.loads(path.read_text())
    doc["dropped"].append(999)
    path.write_text(json.dumps(doc))
    assert validate_run(run, screening_catalog(None))["grouping"]


@pytest.mark.usefixtures("asked_by_model")
def test_an_active_switched_to_an_older_outbox_is_caught(run):
    root = GroupingPaths(run).root / "outbox"
    current = (root / "active").read_text().strip()
    older = root / "0123456789ab"
    older.mkdir()
    (older / "000001.json").write_bytes((root / current / "000001.json").read_bytes())
    (root / "active").write_text("0123456789ab\n")
    assert any("records committed" in p for p in validate_run(run, screening_catalog(None))["grouping"])


def test_a_broken_active_is_reported_not_raised(run):
    (GroupingPaths(run).root / "outbox" / "active").write_text("../elsewhere\n")
    assert any("outbox_active_invalid" in p for p in validate_run(run, screening_catalog(None))["grouping"])


def _charter_path(run):
    root = GroupingPaths(run).root / "outbox"
    return root / (root / "active").read_text().strip() / "charter.json"


def test_each_outbox_charter_is_rehashed_to_its_folder_name(run):
    key = str(_charter_path(run).relative_to(run))
    assert validate_run(run, screening_catalog(None))[key] == []
    doc = json.loads(_charter_path(run).read_text())
    _charter_path(run).write_text(json.dumps({**doc, "system": {**doc["system"], "text": "edited"}}))
    assert "charter_mismatch" in validate_run(run, screening_catalog(None))[key][0]
    _charter_path(run).unlink()
    assert "charter_missing" in validate_run(run, screening_catalog(None))[key][0]


def test_events_jsonl_is_checked_when_present(run):
    events = run / "log" / "events.jsonl"
    assert events.is_file() and validate_run(run, screening_catalog(None))["log/events.jsonl"] == []
    good = json.loads(events.read_text().splitlines()[0])
    with events.open("a") as f:
        f.write(json.dumps({**good, "kind": "guess", "durationMs": "3"}) + "\nnot json\n{\"schemaVersion\": 1")
    problems = validate_run(run, screening_catalog(None))["log/events.jsonl"]
    n = len(events.read_text().splitlines())
    assert f"line {n - 2}: durationMs is str" in problems and any(p.startswith(f"line {n - 2}: kind 'guess'") for p in problems)
    assert any(p.startswith(f"line {n - 1}: does not parse") for p in problems)
    assert f"line {n}: partial, its writer stopped mid-line" in problems
