from dataclasses import replace

import pytest
from helpers import GENERIC, LATENCY, LATENCY_ALLOC, row, summary

from perfrepair.ai.evaluate.worthiness.render import render
from perfrepair.dto.screen import Verdict
from perfrepair.result.evidence import build_evidence
from perfrepair.dto.perf_mode import PerfMode
from perfrepair.result.modes import mode_of
from perfrepair.result.triage import triage

ROWS = [row("a1", "P1"), row("a2", "P2"), row("a1b", "P1", input_size=1024), row("s1", "P3", algorithm="ALG-S"),
        row("u1", "P4", algorithm="ALG-U"), row("u2", "P5", algorithm="ALG-U")]
QUALIFIED = {1: "TypeA|ALG-A|P1", 2: "TypeA|ALG-A|P2", 3: "TypeA|ALG-S|P3", 4: "TypeA|ALG-U|P4", 5: "TypeA|ALG-U|P5"}
GROUPS = {"groups": [{"id": "g-a", "family": "f", "description": "A", "members": [1, 2]},
                     {"id": "g-s", "family": "f", "description": "S", "members": [3]},
                     {"id": "g-u", "family": "f", "description": "U", "members": [4, 5]}],
          "items": {str(k): {"qualified": v} for k, v in QUALIFIED.items()}, "interop": {"status": "not_run", "pairs": []}}
M = {"a1": {"timeNs": summary(200), "allocationCount": summary(10)},
     "a2": {"timeNs": summary(100), "allocationCount": summary(30)},
     "a1b": {"timeNs": summary(900)},
     "s1": {"timeNs": summary(50)},
     "u1": {"timeNs": summary(100)}, "u2": {"timeNs": summary(100)}}
EVIDENCE = {e.groupId: e for e in build_evidence(GROUPS, ROWS, M, None, GENERIC.perf)}


def test_pairs_only_within_one_configuration():
    g = EVIDENCE["g-a"]
    assert g.family == "f" and g.type == "TypeA"
    assert [(c.inputSize, len(c.pairs)) for c in g.configurations] == [(1024, 0), (64, 2)]
    p = next(p for c in g.configurations for p in c.pairs if p.toItem == "TypeA|ALG-A|P2")
    by = {c.metric: c for c in p.metrics}
    assert by["timeNs"].ratio == pytest.approx(0.5) and by["allocationCount"].ratio == pytest.approx(3.0)
    assert by["timeNs"].pImprove == 1.0 and by["timeNs"].level == "ok"


def test_a_fixed_and_a_notfixed_row_are_never_paired_and_the_render_names_the_variant():
    rows = [row("f1", "P1", variant="fixed"), row("n2", "P2")]
    m = {"f1": {"timeNs": summary(10)}, "n2": {"timeNs": summary(100)}}
    g = {e.groupId: e for e in build_evidence(GROUPS, rows, m, None, GENERIC.perf)}["g-a"]
    assert [(c.variant, len(c.members), len(c.pairs)) for c in g.configurations] == [("fixed", 1, 0), ("notFixed", 1, 0)]
    both = [row("f1", "P1", variant="fixed"), row("f2", "P2", variant="fixed")]
    g = {e.groupId: e for e in build_evidence(GROUPS, both, {"f1": m["f1"], "f2": m["n2"]}, None, GENERIC.perf)}["g-a"]
    assert "CONFIGURATION OP1 key 128 input 64 WARM fixed" in render(g, GENERIC, [])


def test_one_selected_metric_improving_is_enough_unless_another_worsens():
    p = next(p for c in EVIDENCE["g-a"].configurations for p in c.pairs if p.toItem == "TypeA|ALG-A|P2")
    assert LATENCY.improves(p) and not LATENCY_ALLOC.improves(p) and not GENERIC.improves(p)
    assert LATENCY.deciding(p).metric == "timeNs"


def test_the_evidence_holds_only_the_selected_metrics():
    alloc = mode_of(PerfMode(("memAlloc",)))
    g = build_evidence(GROUPS, ROWS, M, None, alloc.perf)[0]
    pair = next(p for c in g.configurations for p in c.pairs)
    assert {m for c in g.configurations for s in c.members for m in s.metrics} == {"allocationCount"}
    assert [c.metric for c in pair.metrics] == ["allocationCount"]


def test_triage_asks_only_where_a_pair_improves():
    ask, decided = triage(list(EVIDENCE.values()), LATENCY)
    assert [e.groupId for e in ask] == ["g-a"]
    assert {v.groupId: v.decision for v in decided} == {"g-s": "not_comparable", "g-u": "no_improvement"}
    ask, decided = triage(list(EVIDENCE.values()), LATENCY_ALLOC)
    assert ask == [] and {v.groupId: v.decision for v in decided}["g-u"] == "not_measured"


def _decided(measurements, mode=LATENCY):
    evidence = build_evidence(GROUPS, ROWS, measurements, None, mode.perf)
    ask, decided = triage(evidence, mode)
    return {e.groupId: e for e in ask}, {v.groupId: v.decision for v in decided}


def test_a_gain_below_the_minimum_effect_is_not_an_improvement():
    close = {**M, "a1": {"timeNs": summary(100), "allocationCount": summary(30)},
             "a2": {"timeNs": summary(99), "allocationCount": summary(30)}}
    assert LATENCY.improvingRatio == 0.97
    assert _decided(close)[1]["g-a"] == "no_improvement"


def test_a_gain_inside_the_spread_is_asked_with_its_level_not_refused():
    noisy = {**M, "a1": {"timeNs": summary(100, spread=40.0)},
             "a2": {"timeNs": summary(95, spread=40.0)}}
    ask, _ = _decided(noisy)
    p = next(p for c in ask["g-a"].configurations for p in c.pairs if p.toItem == "TypeA|ALG-A|P2")
    assert 0.5 < p.metrics[0].pImprove < 0.95 and p.metrics[0].level in ("warn", "weak")


def test_missing_allocations_are_not_measured_never_no_improvement():
    unknown = {**M, "a2": {"timeNs": summary(100)}}
    assert _decided(unknown, LATENCY_ALLOC)[1]["g-a"] == "not_measured"
    assert _decided(unknown, LATENCY)[0]["g-a"]
    assert _decided(unknown, GENERIC)[0]["g-a"]


def test_a_selected_metric_without_data_is_no_evidence_never_a_proxy():
    energy = mode_of(PerfMode(("energy", "latency")))
    ask, decided = triage(build_evidence(GROUPS, ROWS, M, None, energy.perf), energy)
    reasons = {v.groupId: v.reason for v in decided}
    assert ask == [] and reasons["g-a"].startswith("no_evidence: energyJ")


def test_a_single_run_has_no_confidence():
    single = {**M, "a1": {"timeNs": summary(200, n=1)}}
    ask, _ = _decided(single)
    p = next(p for c in ask["g-a"].configurations for p in c.pairs if p.toItem == "TypeA|ALG-A|P2")
    time = p.metrics[0]
    assert time.pImprove is None and time.level == "too_few_runs" and time.n == 1


def _checked(result, reason="r"):
    pair = {"id": 1, "group": "g-a", "a": QUALIFIED[2], "b": QUALIFIED[1], "result": result, "reason": reason}
    return {**GROUPS, "interop": {"status": "checked", "pairs": [pair]}}


def test_a_failed_interop_pair_is_never_a_replacement():
    evidence = {e.groupId: e for e in build_evidence(_checked("fail"), ROWS, M, None, GENERIC.perf)}
    assert [len(c.pairs) for c in evidence["g-a"].configurations] == [0, 0]
    ask, decided = triage(list(evidence.values()), LATENCY)
    assert ask == [] and {v.groupId: v.decision for v in decided}["g-a"] == "not_comparable"


def test_interop_labels_ride_on_every_pair():
    assert {p.interop for c in EVIDENCE["g-a"].configurations for p in c.pairs} == {"not_run"}
    kept = build_evidence(_checked("not_checkable"), ROWS, M, None, GENERIC.perf)
    assert {p.interop for e in kept for c in e.configurations for p in c.pairs} == {"not_checkable", "not_planned"}


def test_a_pair_whose_target_lowers_the_status_is_left_out_one_direction_only():
    verdicts = {QUALIFIED[1]: Verdict("accepted", "r", "S", "ALG-A"), QUALIFIED[2]: Verdict("broken", "r", "S", "ALG-B")}
    evidence = {e.groupId: e for e in build_evidence(GROUPS, ROWS, M, verdicts, GENERIC.perf)}
    assert [(p.fromItem, p.toItem) for c in evidence["g-a"].configurations for p in c.pairs] == [
        (QUALIFIED[2], QUALIFIED[1])]


def _energy(kind_from, kind_to):
    m = {**M, "a1": {**M["a1"], "energyJ": replace(summary(4), kind=kind_from)},
         "a2": {**M["a2"], "energyJ": replace(summary(2), kind=kind_to)}}
    g = {e.groupId: e for e in build_evidence(GROUPS, ROWS, m, None, GENERIC.perf)}["g-a"]
    return g, next(p for c in g.configurations for p in c.pairs if p.toItem == "TypeA|ALG-A|P2")


def test_worthiness_sees_energy_when_measured_on_both_sides():
    g, p = _energy("measured", "measured")
    joules = {c.metric: c for c in p.metrics}["energyJ"]
    assert joules.ratio == pytest.approx(0.5) and joules.pImprove == 1.0 and joules.reason is None
    text = render(g, LATENCY, [])
    assert "energyJ median J/op" in text and "| measured" in text and "0.500 | 100% (ok)" in text


def test_energy_of_different_kinds_is_never_compared():
    g, p = _energy("measured", "estimated")
    joules = {c.metric: c for c in p.metrics}["energyJ"]
    assert joules.ratio is None and joules.pImprove is None
    assert joules.reason == "energy_kinds_differ: measured before, estimated after"
    assert "energy_kinds_differ: measured before, estimated after | - | -" in render(g, LATENCY, [])


def test_a_metric_one_side_lacks_is_no_comparison():
    p = next(p for c in EVIDENCE["g-a"].configurations for p in c.pairs if p.toItem == "TypeA|ALG-A|P2")
    assert [c.metric for c in p.metrics] == ["timeNs", "allocationCount"]
