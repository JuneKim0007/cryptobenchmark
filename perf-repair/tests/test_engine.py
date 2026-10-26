import json
from dataclasses import dataclass, field

import pytest
from helpers import QUIET, label_charter

from perfrepair.dto.decision import OutboxRecord
from perfrepair.dto.prompt import TaskPrompt
from perfrepair.orchestrate.agent import AgentRefused, ScriptedConversations
from perfrepair.orchestrate.engine.ask import Limits
from perfrepair.orchestrate.engine.decide import decide
from perfrepair.orchestrate.engine.kind import project
from perfrepair.orchestrate.engine.outbox import Outbox
from perfrepair.validation import ValidationFailed


@dataclass(frozen=True)
class Thing:
    key: str


@dataclass
class Labels:
    seen: dict = field(default_factory=dict)
    version: int = 0


class LabelKind:
    name = "labels"

    def __init__(self, keys=("a", "b", "c")):
        self._items = [Thing(k) for k in keys]

    def items(self):
        return self._items

    def empty(self):
        return Labels()

    def admit(self, item):
        return []

    def label(self, item):
        return item.key

    def render(self, item, state):
        return TaskPrompt(self.name, f"ITEM {item.key}", item.key)

    def check(self, item, text, state):
        label = json.loads(text).get("label", "")
        return ({"label": label}, []) if label else (None, ["label is empty"])

    def apply(self, state, item, record):
        state.seen[item.key] = record.decision["label"] if record.decision else None
        state.version += 1

    def validate(self, state, records):
        return [] if project(self, records) == state else ["state differs from the replay"]

    def write(self, state, records):
        pass


CHARTER = label_charter({"type": "object"})


def label_of(task):
    return task.text.split()[1]


def test_each_item_gets_a_fresh_conversation_and_one_commit(tmp_path):
    agent = ScriptedConversations(lambda m, *_: {"label": label_of(m)})
    state = decide(LabelKind(), CHARTER, agent, tmp_path, **QUIET)
    assert state.seen == {"a": "a", "b": "b", "c": "c"} and agent.started == 3
    assert [r.outcome for r in Outbox(tmp_path / "outbox").records()] == ["decided"] * 3


def test_rejection_reasks_the_same_conversation_then_respawns_then_drops(tmp_path):
    agent = ScriptedConversations(lambda m, conversation, turn: {"label": ""})
    state = decide(LabelKind(("a",)), CHARTER, agent, tmp_path, Limits(turns=2, sessions=2), **QUIET)
    assert agent.started == 2 and len(agent.turns) == 4
    assert "YOUR ANSWER WAS REJECTED" in agent.turns[1][2].text
    record = Outbox(tmp_path / "outbox").records()[0]
    assert record.outcome == "dropped" and len(record.problems) == 4 and state.seen == {"a": None}
    assert json.loads((tmp_path / "errors.jsonl").read_text())["problems"][0].startswith("s1t1")


def test_a_refusal_is_a_failed_turn(tmp_path):
    def refuse(*_):
        raise AgentRefused("declined")
    decide(LabelKind(("a",)), CHARTER, ScriptedConversations(refuse), tmp_path, Limits(turns=1, sessions=1), **QUIET)
    assert "model refused: declined" in Outbox(tmp_path / "outbox").records()[0].problems[0]


def test_a_crash_never_repeats_or_loses_a_decision(tmp_path):
    calls = {"n": 0}

    def flaky(m, *_):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("connection lost")
        return {"label": label_of(m)}
    with pytest.raises(RuntimeError):
        decide(LabelKind(), CHARTER, ScriptedConversations(flaky), tmp_path, **QUIET)
    (tmp_path / "outbox" / "000002.json.tmp").write_text("{half")
    rest = ScriptedConversations(lambda m, *_: {"label": label_of(m)})
    state = decide(LabelKind(), CHARTER, rest, tmp_path, **QUIET)
    assert rest.started == 2 and [r.item for r in Outbox(tmp_path / "outbox").records()] == ["a", "b", "c"]
    assert state.version == 3


def test_a_limit_stops_early_and_the_next_call_resumes(tmp_path):
    agent = ScriptedConversations(lambda m, *_: {"label": label_of(m)})
    decide(LabelKind(), CHARTER, agent, tmp_path, limit=1, **QUIET)
    assert len(Outbox(tmp_path / "outbox").records()) == 1
    decide(LabelKind(), CHARTER, agent, tmp_path, **QUIET)
    assert len(Outbox(tmp_path / "outbox").records()) == 3


def test_an_inconsistent_state_stops_the_engine(tmp_path):
    kind = LabelKind()
    kind.validate = lambda state, records: ["broken"]
    with pytest.raises(ValidationFailed, match="broken"):
        decide(kind, CHARTER, ScriptedConversations(lambda *_: {"label": "x"}), tmp_path, **QUIET)


def test_the_outbox_commits_whole_records_once_and_in_order(tmp_path):
    box = Outbox(tmp_path / "outbox").open()
    first = OutboxRecord(1, "a", "decided", 1, 1, {"label": "a"})
    assert box.append(first) == first
    with pytest.raises(FileExistsError):
        box.append(first)
    (tmp_path / "outbox" / "000003.json").write_text(json.dumps(OutboxRecord(3, "c", "dropped", 1, 1).to_json()))
    with pytest.raises(ValueError, match="expected record 2"):
        box.records()
    with pytest.raises(ValueError, match="carries a decision"):
        OutboxRecord.from_json({**first.to_json(), "decision": None})
