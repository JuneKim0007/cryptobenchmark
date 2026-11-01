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
          "items": {str(k): {"qualified": v} for k, v in QUALIFIED.items()}, "interop": {"status": "not_run", "pairs": []}}
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
    assert p.timeRatio == pytest.approx(0.5) and p.allocationRatio == pytest.approx(3.0) and p.pImprove == 1.0 and p.level == "ok"


def test_modes_differ_only_on_allocations():
    p = next(p for c in EVIDENCE["g-a"].configurations for p in c.pairs if p.toItem == "TypeA|ALG-A|P2")
    assert MODES["latency"].improves(p) and not MODES["battery"].improves(p)


def test_triage_asks_only_where_a_pair_improves():
    ask, decided = triage(list(EVIDENCE.values()), MODES["latency"])
    assert [e.groupId for e in ask] == ["g-a"]
    assert {v.groupId: v.decision for v in decided} == {"g-s": "not_comparable", "g-u": "no_improvement"}
    ask, decided = triage(list(EVIDENCE.values()), MODES["battery"])
    assert ask == [] and all(v.proxy for v in decided)


def _decided(measurements, mode="latency"):
    evidence = build_evidence(GROUPS, ROWS, measurements)
    ask, decided = triage(evidence, MODES[mode])
    return {e.groupId: e for e in ask}, {v.groupId: v.decision for v in decided}


def test_a_gain_below_the_minimum_effect_is_not_an_improvement():
    close = {**M, "a1": {"timeNs": summary(100), "allocations": summary(30)},
             "a2": {"timeNs": summary(99), "allocations": summary(30)}}
    assert MODES["latency"].improvingRatio == 0.97
    assert _decided(close)[1]["g-a"] == "no_improvement"


def test_a_gain_inside_the_spread_is_asked_with_its_level_not_refused():
    noisy = {**M, "a1": {"timeNs": summary(100, spread=40.0), "allocations": None},
             "a2": {"timeNs": summary(95, spread=40.0), "allocations": None}}
    ask, _ = _decided(noisy)
    p = next(p for c in ask["g-a"].configurations for p in c.pairs if p.toItem == "TypeA|ALG-A|P2")
    assert 0.5 < p.pImprove < 0.95 and p.level in ("warn", "weak")


def test_missing_allocations_are_not_measured_never_no_improvement():
    unknown = {**M, "a2": {"timeNs": summary(100), "allocations": None}}
    assert _decided(unknown, "battery")[1]["g-a"] == "not_measured"
    assert _decided(unknown, "latency")[0]["g-a"]


def test_a_single_run_has_no_confidence():
    single = {**M, "a1": {"timeNs": summary(200, n=1), "allocations": None}}
    ask, _ = _decided(single)
    p = next(p for c in ask["g-a"].configurations for p in c.pairs if p.toItem == "TypeA|ALG-A|P2")
    assert p.pImprove is None and p.level == "too_few_runs" and p.n == 1


def _checked(result, reason="r"):
    pair = {"id": 1, "group": "g-a", "a": QUALIFIED[2], "b": QUALIFIED[1], "result": result, "reason": reason}
    return {**GROUPS, "interop": {"status": "checked", "pairs": [pair]}}


def test_a_failed_interop_pair_is_never_a_replacement():
    evidence = {e.groupId: e for e in build_evidence(_checked("fail"), ROWS, M)}
    assert [len(c.pairs) for c in evidence["g-a"].configurations] == [0, 0]
    ask, decided = triage(list(evidence.values()), MODES["latency"])
    assert ask == [] and {v.groupId: v.decision for v in decided}["g-a"] == "not_comparable"


def test_interop_labels_ride_on_every_pair():
    assert {p.interop for c in EVIDENCE["g-a"].configurations for p in c.pairs} == {"not_run"}
    kept = build_evidence(_checked("not_checkable"), ROWS, M)
    assert {p.interop for e in kept for c in e.configurations for p in c.pairs} == {"not_checkable", "not_planned"}


def test_groups_without_an_interop_section_are_refused():
    with pytest.raises(ValueError, match="no interop section"):
        build_evidence({k: v for k, v in GROUPS.items() if k != "interop"}, ROWS, M)
