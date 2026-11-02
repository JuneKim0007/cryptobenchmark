import hashlib
import json
import logging
from dataclasses import replace

import pytest
from helpers import label_charter
from test_engine import LabelKind, label_of

from perfrepair.ai.runtime.gateway.spawn import Spawned
from perfrepair.dto.decision import AgentIdentity, OutboxRecord
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.runtime.engine.decide import decide
from perfrepair.ai.runtime.engine.outbox import NoOutbox, OutboxError, active_fingerprint, active_outbox

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
    return [line for line in lines if line.startswith("charter changed")]


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
    assert changes(lines) == [f"charter changed: outbox {V1.fingerprint} → {V2.fingerprint} "
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
    assert changes(lines) == [f"charter changed: outbox {V2.fingerprint} → {V1.fingerprint} "
                              f"(3 records kept in {V2.fingerprint}, 2 resumed)"]
    assert hashes(tmp_path / "outbox" / V2.fingerprint) == newer
    agent, _ = run(tmp_path, V2)
    assert agent.started == 0 and saved(tmp_path) == {"a": "A", "b": "B", "c": "C"}


def test_records_outside_a_fingerprint_folder_are_an_error(tmp_path):
    flat = tmp_path / "outbox"
    flat.mkdir()
    (flat / "000001.json").write_text(json.dumps(OutboxRecord(1, "a", "decided", 1, 1, {"label": "old"}).to_json()))
    with pytest.raises(OutboxError, match="outbox_unversioned"):
        active_outbox(tmp_path)
    with pytest.raises(OutboxError, match="outbox_unversioned"):
        run(tmp_path, V1)


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
    assert active_fingerprint(tmp_path) is None and isinstance(active_outbox(tmp_path), NoOutbox)
    assert active_outbox(tmp_path).records() == []


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


def test_run_inputs_join_the_fingerprint_and_none_keep_it():
    with_inputs = replace(V1, inputs="1 broken")
    assert with_inputs.fingerprint != V1.fingerprint == replace(V1, inputs="").fingerprint
    assert replace(V1, inputs="1 accepted").fingerprint != with_inputs.fingerprint


OPUS = AgentIdentity("claude", "opus", "low")
HAIKU = AgentIdentity("claude", "haiku", "low")


def spawned(identity):
    return Spawned(ScriptedConversations(lambda m, *_: {"label": label_of(m)}), identity)


def records(root):
    return active_outbox(root).records()


def test_each_record_carries_the_gateway_model_and_effort_that_answered_it(tmp_path):
    decide(SavedKind(tmp_path), V1, spawned(OPUS), tmp_path, limit=1, echo=lambda _: None)
    first = records(tmp_path)[0]
    assert first.agent == OPUS
    on_disk = json.loads(active_outbox(tmp_path).path(1).read_text())
    assert on_disk["schemaVersion"] == 2 and (on_disk["gateway"], on_disk["model"], on_disk["effort"]) == ("claude", "opus", "low")


def test_a_resume_with_other_values_logs_one_line_naming_both_and_keeps_the_outbox(tmp_path, caplog):
    decide(SavedKind(tmp_path), V1, spawned(OPUS), tmp_path, limit=1, echo=lambda _: None)
    before = active_fingerprint(tmp_path)
    with caplog.at_level(logging.WARNING, logger="perfrepair"):
        decide(SavedKind(tmp_path), V1, spawned(HAIKU), tmp_path, limit=1, echo=lambda _: None)
    assert active_fingerprint(tmp_path) == before
    assert [r.agent for r in records(tmp_path)] == [OPUS, HAIKU]
    assert caplog.messages == [f"mixed_agents: outbox {before} holds answers from claude/opus/low, now asking claude/haiku/low"]


def test_a_resume_with_the_same_values_or_nothing_left_to_ask_is_silent(tmp_path, caplog):
    with caplog.at_level(logging.WARNING, logger="perfrepair"):
        decide(SavedKind(tmp_path), V1, spawned(OPUS), tmp_path, limit=1, echo=lambda _: None)
        decide(SavedKind(tmp_path), V1, spawned(OPUS), tmp_path, echo=lambda _: None)
        decide(SavedKind(tmp_path), V1, spawned(HAIKU), tmp_path, echo=lambda _: None)
    assert caplog.messages == []


def test_old_records_without_the_fields_stay_readable_and_do_not_warn(tmp_path, caplog):
    decide(SavedKind(tmp_path), V1, spawned(OPUS), tmp_path, limit=1, echo=lambda _: None)
    path = active_outbox(tmp_path).path(1)
    old = {k: v for k, v in json.loads(path.read_text()).items() if k not in ("gateway", "model", "effort")}
    path.write_text(json.dumps({**old, "schemaVersion": 1}))
    assert records(tmp_path)[0].agent == AgentIdentity()
    with caplog.at_level(logging.WARNING, logger="perfrepair"):
        decide(SavedKind(tmp_path), V1, spawned(HAIKU), tmp_path, echo=lambda _: None)
    assert caplog.messages == [] and records(tmp_path)[-1].agent == HAIKU


def test_an_unknown_record_version_is_refused():
    with pytest.raises(ValueError, match="schemaVersion 3 is not one of"):
        OutboxRecord.from_json({"schemaVersion": 3, "outcome": "dropped", "seq": 1})
