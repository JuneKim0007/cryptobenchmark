import hashlib
import json

import pytest
from helpers import label_charter
from test_engine import LabelKind, label_of

from perfrepair.dto.decision import OutboxRecord
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.runtime.engine.decide import decide
from perfrepair.ai.runtime.engine.outbox import LEGACY, OutboxError, active_fingerprint, active_outbox

V1 = label_charter({"type": "object"})
V2 = label_charter({"type": "object", "title": "v2"})


class SavedKind(LabelKind):
    def __init__(self, root):
        super().__init__()
        self.root = root

    def write(self, state, records):
        (self.root / "state.json").write_text(json.dumps(state.seen))


def run(root, charter, answer=label_of, limit=None, crash_at=None):
    lines, calls = [], {"n": 0}

    def reply(m, *_):
        calls["n"] += 1
        if calls["n"] == crash_at:
            raise RuntimeError("connection lost")
        return {"label": answer(m)}
    agent = ScriptedConversations(reply)
    decide(SavedKind(root), charter, agent, root, limit=limit, echo=lines.append)
    return agent, lines


def hashes(directory):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(directory.iterdir()) if p.is_file()}


def changes(lines):
    return [line for line in lines if line.startswith("prompt changed")]


def saved(root):
    return json.loads((root / "state.json").read_text())


def test_the_fingerprints_differ():
    assert V1.fingerprint != V2.fingerprint


def test_a_first_run_opens_the_fingerprint_outbox_and_marks_it_active(tmp_path):
    _, lines = run(tmp_path, V1)
    box = tmp_path / "outbox" / V1.fingerprint
    assert sorted(p.name for p in box.iterdir()) == ["000001.json", "000002.json", "000003.json"]
    assert (tmp_path / "outbox" / "active").read_text() == V1.fingerprint + "\n"
    assert active_outbox(tmp_path).fingerprint == V1.fingerprint and not changes(lines)
    journal = [json.loads(line) for line in (tmp_path / "journal.jsonl").read_text().splitlines()]
    assert {j["charter"] for j in journal} == {V1.fingerprint}


def test_the_same_prompt_resumes_its_outbox(tmp_path):
    run(tmp_path, V1, limit=1)
    agent, lines = run(tmp_path, V1)
    assert agent.started == 2 and not changes(lines) and len(active_outbox(tmp_path).records()) == 3


def test_a_changed_prompt_starts_a_new_outbox_and_leaves_the_old_byte_for_byte(tmp_path):
    run(tmp_path, V1)
    old = tmp_path / "outbox" / V1.fingerprint
    before = hashes(old)
    agent, lines = run(tmp_path, V2, answer=lambda m: label_of(m).upper())
    assert hashes(old) == before and agent.started == 3
    assert changes(lines) == [f"prompt changed: outbox {V1.fingerprint} → {V2.fingerprint} "
                              f"(3 records kept in {V1.fingerprint}, 0 resumed)"]
    assert saved(tmp_path) == {"a": "A", "b": "B", "c": "C"}
    journal = [json.loads(line)["charter"] for line in (tmp_path / "journal.jsonl").read_text().splitlines()]
    assert journal == [V1.fingerprint] * 3 + [V2.fingerprint] * 3


def test_reverting_resumes_the_old_outbox_and_rebuilds_the_projections(tmp_path):
    run(tmp_path, V1, limit=2)
    run(tmp_path, V2, answer=lambda m: label_of(m).upper())
    newer = hashes(tmp_path / "outbox" / V2.fingerprint)
    agent, lines = run(tmp_path, V1)
    assert agent.started == 1 and saved(tmp_path) == {"a": "a", "b": "b", "c": "c"}
    assert changes(lines) == [f"prompt changed: outbox {V2.fingerprint} → {V1.fingerprint} "
                              f"(3 records kept in {V2.fingerprint}, 2 resumed)"]
    assert hashes(tmp_path / "outbox" / V2.fingerprint) == newer
    agent, _ = run(tmp_path, V2)
    assert agent.started == 0 and saved(tmp_path) == {"a": "A", "b": "B", "c": "C"}


def test_a_flat_outbox_reads_as_legacy_and_is_never_touched(tmp_path):
    flat = tmp_path / "outbox"
    flat.mkdir()
    for seq, key in ((1, "a"), (2, "b")):
        (flat / f"{seq:06d}.json").write_text(json.dumps(OutboxRecord(seq, key, "decided", 1, 1, {"label": "old"}).to_json()))
    before = hashes(flat)
    assert active_fingerprint(tmp_path) == LEGACY and len(active_outbox(tmp_path).records()) == 2
    agent, lines = run(tmp_path, V1)
    assert agent.started == 3 and changes(lines) == [
        f"prompt changed: outbox legacy → {V1.fingerprint} (2 records kept in legacy, 0 resumed)"]
    assert {k: v for k, v in hashes(flat).items() if k != "active"} == before
    (flat / "active").write_text(LEGACY + "\n")
    assert [r.decision for r in active_outbox(tmp_path).records()] == [{"label": "old"}] * 2
    agent, lines = run(tmp_path, V1)
    assert agent.started == 0 and changes(lines)[0].startswith(f"prompt changed: outbox legacy → {V1.fingerprint}")


def test_a_crash_on_a_new_fingerprint_resumes_it_without_touching_the_old(tmp_path):
    run(tmp_path, V1)
    before = hashes(tmp_path / "outbox" / V1.fingerprint)
    with pytest.raises(RuntimeError):
        run(tmp_path, V2, crash_at=2)
    (tmp_path / "outbox" / V2.fingerprint / "000002.json.tmp").write_text("{half")
    agent, lines = run(tmp_path, V2)
    assert agent.started == 2 and not changes(lines)
    assert [r.item for r in active_outbox(tmp_path).records()] == ["a", "b", "c"]
    assert hashes(tmp_path / "outbox" / V1.fingerprint) == before


def test_nothing_committed_resolves_to_an_empty_outbox(tmp_path):
    assert active_fingerprint(tmp_path) is None and active_outbox(tmp_path).records() == []


def test_an_active_file_naming_a_missing_folder_is_an_error(tmp_path):
    (tmp_path / "outbox").mkdir()
    (tmp_path / "outbox" / "active").write_text("0123456789ab\n")
    with pytest.raises(OutboxError, match="outbox_missing"):
        active_outbox(tmp_path)
    with pytest.raises(OutboxError, match="outbox_missing"):
        run(tmp_path, V1)
    (tmp_path / "outbox" / "active").write_text("../elsewhere\n")
    with pytest.raises(OutboxError, match="outbox_active_invalid"):
        active_outbox(tmp_path)
