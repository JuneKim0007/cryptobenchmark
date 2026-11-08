"""The engine's events: one per attempt, pointing at its log/ai/<job>.yaml entry, with tokens, cost and turn counts."""
import json

from helpers import QUIET, logged
from test_engine import CHARTER, LabelKind, label_of

from perfrepair import run_dir as rd
from perfrepair.ai.runtime.agent.conversation import LifetimeGuarded
from perfrepair.ai.runtime.agent.reply import AgentReply
from perfrepair.ai.runtime.engine.decide import decide
from perfrepair.ai.log.where import Where
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


def test_each_attempt_is_one_event_pointing_to_its_log_entry_with_no_text(tmp_path):
    (tmp_path / "role").mkdir()
    events = _events(tmp_path)
    attempts = [e for e in events if e.event == "decision"]
    entries = logged(tmp_path / "role", "labels")
    assert [(e.item, e.outcome, e.data["calls"], e.data["rejected"]) for e in attempts] == [
        ("a", "decided", 2, 1), ("b", "decided", 1, 0), ("c", "decided", 1, 0)]
    for n, e in enumerate(attempts, 1):
        assert e.ref == f"log/ai/labels.yaml#{n}" and entries[n - 1]["item"] == e.item
        assert e.kind == "model" and (e.stage, e.step) == ("grouping", "assign")
        assert "ITEM" not in json.dumps(e.to_json())
    assert attempts[0].costUsd == 0.02 and attempts[0].tokens["input"] == 200
    assert attempts[0].data["problems"] == ["label is empty"]


def test_a_step_starts_with_what_is_pending_and_ends_with_counts(tmp_path):
    (tmp_path / "role").mkdir()
    first = [e for e in _events(tmp_path, limit=2) if e.stage == "grouping"]
    start, end = first[0], first[-1]
    assert (start.event, start.outcome, start.data["pending"]) == ("start", "opened", 2)
    assert end.event == "end" and end.data["counts"] == {"decided": 2, "dropped": 0, "committed": 2, "left": 1}
    again = _events(tmp_path)
    started = [e for e in again if e.event == "start"][-1]
    assert (started.outcome, started.data["committed"], started.data["pending"]) == ("resumed", 2, 1)
    assert len(logged(tmp_path / "role", "labels")) == 3
