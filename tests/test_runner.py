"""The generic decision loop, driven by a minimal decision kind: fresh call per item, retry, fallback, resume."""
import json
from dataclasses import dataclass, field

import pytest

from perfrepair.orchestrate import journal
from perfrepair.orchestrate.agent import ScriptedAgent
from perfrepair.orchestrate.decisions.kind import Checked
from perfrepair.orchestrate.runner import RunPaths, run

QUIET = {"echo": lambda _: None}


@dataclass(frozen=True)
class Thing:
    itemId: str


@dataclass
class Tally:
    seen: dict = field(default_factory=dict)

    def to_json(self):
        return {"seen": self.seen}


class Labels:
    """Decision kind: the agent labels each item; the gate accepts any non-empty label."""
    name, prompt, schema = "labels", "SYS", {"type": "object"}

    def render(self, item, state, refused):
        return f"ITEM {item.itemId}" + (f"\nREFUSED: {refused}" if refused else "")

    def validate(self, item, text, state):
        label = json.loads(text).get("label", "")
        return Checked(label) if label else Checked(problems=["label is empty"])

    def apply(self, item, decision, state):
        state.seen[item.itemId] = decision
        return {"label": decision}

    def fallback(self, item, problems):
        return "fallback"

    def decision_json(self, decision):
        return {"label": decision}

    def decision_from_json(self, doc):
        return doc["label"]


ITEMS = [Thing("a"), Thing("b"), Thing("c")]


def go(agent, tmp_path, state=None, **kw):
    return run(Labels(), ITEMS, agent, state or Tally(), RunPaths.under(tmp_path, "labels"), **(QUIET | kw))


def test_one_fresh_call_per_item(tmp_path):
    agent = ScriptedAgent(lambda user: {"label": user.split()[1]})
    state = go(agent, tmp_path)
    assert state.seen == {"a": "a", "b": "b", "c": "c"}
    assert [u for _, u in agent.calls] == ["ITEM a", "ITEM b", "ITEM c"]
    assert [e["status"] for e in journal.read(tmp_path / "labels.journal.jsonl")] == ["applied"] * 3


def test_refused_twice_falls_back(tmp_path):
    agent = ScriptedAgent(lambda user: {"label": ""})
    state = go(agent, tmp_path)
    assert "REFUSED" in agent.calls[1][1]
    assert set(state.seen.values()) == {"fallback"}


def test_resumes_after_a_crash(tmp_path):
    n = {"calls": 0}

    def flaky(user):
        n["calls"] += 1
        if n["calls"] == 2:
            raise RuntimeError("connection lost")
        return {"label": "x"}
    with pytest.raises(RuntimeError):
        go(ScriptedAgent(flaky), tmp_path)
    agent = ScriptedAgent(lambda user: {"label": "y"})
    go(agent, tmp_path)
    assert len(agent.calls) == 2
