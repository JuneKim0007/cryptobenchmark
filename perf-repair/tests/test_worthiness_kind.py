import json

import pytest
from helpers import summary
from test_evidence import EVIDENCE, GROUPS, M, ROWS

from perfrepair.dto import Verdicts
from perfrepair.dto.perf_mode import PerfMode
from perfrepair.dto.units import DisplayUnits
from perfrepair.result.modes import mode_of
from perfrepair.ai.evaluate.worthiness.kind import WorthinessKind
from perfrepair.result.evidence import build_evidence
from helpers import LATENCY, LATENCY_ALLOC

KIND = WorthinessKind(LATENCY, ["cpu_not_locked: ..."], list(EVIDENCE.values()), ".")
G = EVIDENCE["g-a"]
P1, P2 = "M1", "M2"  # aliases of TypeA|ALG-A|P1, TypeA|ALG-A|P2


def reply(decision="test", pairs=None, reason="r"):
    return json.dumps({"decision": decision, "pairs": pairs if pairs is not None else [], "reason": reason})


def test_render_carries_numbers_mode_and_warnings():
    text = KIND.render(G, Verdicts("latency")).text
    assert "MODE: latency" in text and "cpu_not_locked" in text and "0.500" in text
    assert "input 1024" not in text


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


def test_gate_refuses_a_pair_whose_selected_allocations_worsen():
    kind = WorthinessKind(LATENCY_ALLOC, [], list(EVIDENCE.values()), ".")
    _, problems = kind.check(G, reply(pairs=[{"from": P1, "to": P2, "reason": "x"}]), Verdicts(LATENCY_ALLOC.name))
    assert any("does not improve" in p for p in problems)


def test_render_and_verdict_carry_the_graded_confidence():
    assert "100% (ok)" in KIND.render(G, Verdicts("latency")).text
    decision, _ = KIND.check(G, reply(pairs=[{"from": P1, "to": P2, "reason": "2x"}]), Verdicts("latency"))
    assert (decision["pairs"][0]["pImprove"], decision["pairs"][0]["level"]) == (1.0, "ok")


def test_gate_names_missing_selected_allocations_as_unmeasured():
    unknown = {**M, "a2": {"timeNs": summary(100)}}
    evidence = {e.groupId: e for e in build_evidence(GROUPS, ROWS, unknown, None, LATENCY_ALLOC.perf)}
    kind = WorthinessKind(LATENCY_ALLOC, [], list(evidence.values()), ".")
    _, problems = kind.check(evidence["g-a"], reply(pairs=[{"from": P1, "to": P2, "reason": "x"}]), Verdicts(LATENCY_ALLOC.name))
    assert any("lacks the measurements" in p for p in problems)


def test_time_is_shown_in_the_display_units_and_throughput_only_when_selected():
    both = WorthinessKind(mode_of(PerfMode.parse("latency,throughput")), [], list(EVIDENCE.values()), ".",
                          DisplayUnits("us", "MiB/s"))
    text = both.render(G, Verdicts("x")).text
    assert "timeNs median us/op" in text and "throughput MiB/s (median)" in text and "| 0.2 |" in text
    assert "throughput" not in KIND.render(G, Verdicts("latency")).text.split("CONFIGURATION", 1)[1]
