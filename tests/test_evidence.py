from perfrepair.data_handler.inbound.results import median_interval
import pytest
from helpers import row, summary

from perfrepair.result.evidence import build_evidence
from perfrepair.result.modes import MODES
from perfrepair.result.triage import triage

ROWS = [row("a1", "P1"), row("a2", "P2"), row("a1b", "P1", input_size=1024), row("s1", "P3", algorithm="ALG-S"),
        row("u1", "P4", algorithm="ALG-U"), row("u2", "P5", algorithm="ALG-U")]
QUALIFIED = {1: "TypeA|ALG-A|P1", 2: "TypeA|ALG-A|P2", 3: "TypeA|ALG-S|P3", 4: "TypeA|ALG-U|P4", 5: "TypeA|ALG-U|P5"}
GROUPS = {"groups": [{"id": "g-a", "family": "f", "description": "A", "members": [1, 2]},
                     {"id": "g-s", "family": "f", "description": "S", "members": [3]},
                     {"id": "g-u", "family": "f", "description": "U", "members": [4, 5]}],
          "items": {str(k): {"qualified": v} for k, v in QUALIFIED.items()}}
M = {"a1": {"timeNs": summary(200), "allocations": summary(10)},
     "a2": {"timeNs": summary(100), "allocations": summary(30)},
     "a1b": {"timeNs": summary(900), "allocations": None},
     "s1": {"timeNs": summary(50), "allocations": None},
     "u1": {"timeNs": summary(100), "allocations": None}, "u2": {"timeNs": summary(100), "allocations": None}}
EVIDENCE = {e.groupId: e for e in build_evidence(GROUPS, ROWS, M)}


def test_pairs_only_within_one_configuration():
    g = EVIDENCE["g-a"]
    assert g.family == "f" and g.type == "TypeA"
    assert [(c.inputSize, len(c.pairs)) for c in g.configurations] == [(1024, 0), (64, 2)]
    p = next(p for c in g.configurations for p in c.pairs if p.toItem == "TypeA|ALG-A|P2")
    assert p.timeRatio == pytest.approx(0.5) and p.allocationRatio == pytest.approx(3.0) and not p.ciOverlap


def test_modes_differ_only_on_allocations():
    p = next(p for c in EVIDENCE["g-a"].configurations for p in c.pairs if p.toItem == "TypeA|ALG-A|P2")
    assert MODES["latency"].improves(p) and not MODES["battery"].improves(p)


def test_triage_asks_only_where_a_pair_improves():
    ask, decided = triage(list(EVIDENCE.values()), MODES["latency"])
    assert [e.groupId for e in ask] == ["g-a"]
    assert {v.groupId: v.decision for v in decided} == {"g-s": "not_comparable", "g-u": "no_improvement"}
    ask, decided = triage(list(EVIDENCE.values()), MODES["battery"])
    assert ask == [] and all(v.proxy for v in decided)


def test_differences_inside_the_median_interval_never_reach_the_model():
    close = {**M, "a1": {"timeNs": summary(100, spread=8.0), "allocations": summary(30)},
             "a2": {"timeNs": summary(99, spread=8.0), "allocations": summary(30)}}
    evidence = {e.groupId: e for e in build_evidence(GROUPS, ROWS, close)}
    ask, decided = triage(list(evidence.values()), MODES["latency"])
    assert {v.groupId: v.decision for v in decided}.get("g-a") == "within_noise"


def test_median_interval_uses_order_statistics():
    assert median_interval([float(v) for v in range(1, 51)]) == (18.0, 33.0)
    assert median_interval([1.0, 2.0, 3.0]) == (1.0, 3.0)
