"""The engine's events: one per model turn and per decision, tokens and cost from the reply, refs into journal and outbox."""
import json

from helpers import QUIET
from test_engine import CHARTER, LabelKind, label_of

from perfrepair import run_dir as rd
from perfrepair.ai.runtime.agent.conversation import LifetimeGuarded
from perfrepair.ai.runtime.agent.reply import AgentReply
from perfrepair.ai.runtime.engine.decide import decide
from perfrepair.ai.runtime.engine.events import Where
from perfrepair.log import attach
from perfrepair.log.read import read_events


class Billed:
    """Turn 1 of item a answers empty (rejected); every other turn answers its item; each costs $0.01."""

    def start(self, system, schema):
        return _Billed(system)


class _Billed(LifetimeGuarded):
    def _send(self, message):
        label = "" if self.task.item == "a" and message is self.task else label_of(self.task)
        return AgentReply(json.dumps({"label": label}), "m", "r",
                          {"input": 100, "output": 10, "cacheRead": 50, "cacheWrite": 0, "costUsd": 0.01})


def _events(tmp_path, **kw):
    attach()
    attach(tmp_path)
    decide(LabelKind(), CHARTER, Billed(), tmp_path / "role", where=Where("grouping", "assign"), **QUIET, **kw)
    return read_events(tmp_path / rd.EVENTS)


def test_each_turn_is_one_event_pointing_to_its_journal_line(tmp_path):
    (tmp_path / "role").mkdir()
    events = _events(tmp_path)
    turns = [e for e in events if e.event == "turn"]
    journal = (tmp_path / "role" / "journal.jsonl").read_text().splitlines()
    assert [(e.item, e.outcome) for e in turns] == [("a", "rejected"), ("a", "accepted"), ("b", "accepted"),
                                                    ("c", "accepted")]
    for e in turns:
        path, line = e.ref.rsplit(":", 1)
        entry = json.loads(journal[int(line) - 1])
        assert path == "role/journal.jsonl" and entry["item"] == e.item and entry["status"] == e.outcome
        assert e.kind == "model" and (e.stage, e.step) == ("grouping", "assign") and e.costUsd == 0.01
        assert e.tokens == {"input": 100, "output": 10, "cacheRead": 50, "cacheWrite": 0}
        assert "reply" not in e.data and "ITEM" not in json.dumps(e.to_json())
    assert turns[0].data["problems"] == ["label is empty"] and turns[0].data["session"] == 1


def test_each_decision_sums_its_turns_and_names_its_outbox_record(tmp_path):
    (tmp_path / "role").mkdir()
    events = _events(tmp_path)
    decisions = [e for e in events if e.event == "decision"]
    assert [(e.item, e.outcome, e.data["turns"]) for e in decisions] == [("a", "decided", 2), ("b", "decided", 1),
                                                                        ("c", "decided", 1)]
    fingerprint = CHARTER.fingerprint
    assert decisions[0].ref == f"role/outbox/{fingerprint}/000001.json" and decisions[0].costUsd == 0.02
    assert decisions[0].tokens["input"] == 200 and decisions[0].data["outbox"] == fingerprint


def test_a_step_starts_with_what_is_pending_and_ends_with_counts(tmp_path):
    (tmp_path / "role").mkdir()
    first = [e for e in _events(tmp_path, limit=2) if e.stage == "grouping"]
    start, end = first[0], first[-1]
    assert (start.event, start.outcome, start.data["pending"]) == ("start", "opened", 2)
    assert end.event == "end" and end.data["counts"] == {"decided": 2, "dropped": 0, "committed": 2, "left": 1}
    again = _events(tmp_path)
    started = [e for e in again if e.event == "start"][-1]
    assert (started.outcome, started.data["committed"], started.data["pending"]) == ("resumed", 2, 1)
    assert [e.ref.rsplit(":", 1)[1] for e in again if e.event == "turn"][-1] == "4"
