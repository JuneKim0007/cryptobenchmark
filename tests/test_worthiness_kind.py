import json

import pytest
from test_evidence import EVIDENCE

from perfrepair.dto import Verdicts
from perfrepair.orchestrate.decisions.worthiness import WorthinessKind
from perfrepair.result.modes import MODES

KIND = WorthinessKind(MODES["latency"], ["cpu_not_locked: ..."], list(EVIDENCE.values()), ".", prompt="")
G = EVIDENCE["g-a"]
P1, P2 = "M1", "M2"  # aliases of TypeA|ALG-A|P1, TypeA|ALG-A|P2


def reply(decision="test", pairs=None, reason="r"):
    return json.dumps({"decision": decision, "pairs": pairs if pairs is not None else [], "reason": reason})


def test_render_carries_numbers_mode_and_warnings():
    text = KIND.render(G, Verdicts("latency"))
    assert "MODE: latency" in text and "cpu_not_locked" in text and "0.500" in text
    assert "input 1024" not in text  # a configuration without pairs is not shown


@pytest.mark.parametrize("answer, problem", [
    (reply(pairs=[{"from": P1, "to": P2, "reason": "2x"}]), None),
    (reply(pairs=[{"from": P2, "to": P1, "reason": "x"}]), "does not improve"),
    (reply(pairs=[{"from": P1, "to": "ghost", "reason": "x"}]), "not two different members"),
    (reply(pairs=[]), "test names no pair"),
    (reply("skip", pairs=[{"from": P1, "to": P2, "reason": "x"}]), "skip names pairs"),
    (reply("skip", reason=""), "reason is empty"),
])
def test_gate(answer, problem):
    decision, problems = KIND.check(G, answer, Verdicts("latency"))
    if problem is None:
        assert decision["decision"] == "test" and decision["source"] == "llm"
        assert decision["pairs"][0]["to"] == "TypeA|ALG-A|P2"
    else:
        assert decision is None and any(problem in p for p in problems)


def test_battery_gate_refuses_a_pair_that_allocates_more():
    kind = WorthinessKind(MODES["battery"], [], list(EVIDENCE.values()), ".", prompt="")
    _, problems = kind.check(G, reply(pairs=[{"from": P1, "to": P2, "reason": "x"}]), Verdicts("battery"))
    assert any("does not improve" in p for p in problems)
