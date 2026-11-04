import json
import random
from dataclasses import replace

import pytest
from helpers import summary

from perfrepair.data_handler.inbound.bootstrap import median_interval
from perfrepair.data_handler.inbound.results import read_results
from perfrepair.result.confidence import describe, level
from perfrepair.result.estimate import compare, p_improve

RNG = random.Random(7)


def process(level_, n=50, sd=0.5):
    return tuple(level_ + RNG.gauss(0, sd) for _ in range(n))


BEFORE = (process(100), process(112), process(90))
AFTER = (process(98), process(110), process(88))


def flat(processes):
    return (tuple(v for p in processes for v in p),)


def test_a_clear_win_is_near_certain_and_identical_data_is_a_coin_flip():
    assert p_improve((process(100),), (process(50),)) > 0.99
    same = process(100)
    assert p_improve((same,), (same,)) == pytest.approx(0.5, abs=0.05)


def test_fewer_than_two_runs_give_no_probability():
    assert p_improve(((100.0,),), (process(50),)) is None
    c = compare(summary(100, n=1), summary(50))
    assert c.pImprove is None and c.reason is None and c.n == 1 and c.ratio == 0.5


def test_compare_is_the_one_rule_for_zero_medians_kinds_and_orientation():
    zero = compare(summary(0), summary(5))
    assert zero.ratio is None and zero.reason.startswith("zero_median: ") and zero.pImprove is not None and zero.comparable
    kinds = compare(replace(summary(100), kind="measured"), replace(summary(50), kind="estimated"))
    assert (kinds.ratio, kinds.pImprove, kinds.n, kinds.comparable) == (None, None, 0, False)
    assert kinds.reason == "energy_kinds_differ: measured before, estimated after"
    higher = compare(summary(100), summary(200), lower_is_better=False)
    assert higher.ratio == 0.5 and higher.pImprove > 0.99


def test_resampling_by_process_widens_what_concatenated_runs_hide():
    by_process, concatenated = p_improve(BEFORE, AFTER), p_improve(flat(BEFORE), flat(AFTER))
    assert by_process < concatenated - 0.1 and by_process < 0.8


def test_the_bootstrap_is_deterministic():
    assert p_improve(BEFORE, AFTER) == p_improve(BEFORE, AFTER)
    assert median_interval(BEFORE) == median_interval(BEFORE)


def test_the_interval_is_honest_about_small_samples():
    assert median_interval(((5.0,),)) == (None, None)
    low, high = median_interval((tuple(float(v) for v in range(1, 51)),))
    assert low < 25.5 < high and high - low > 0


@pytest.mark.parametrize("p, name", [(0.99, "ok"), (0.95, "ok"), (0.83, "warn"), (0.8, "warn"), (0.5, "weak"),
                                     (None, "too_few_runs")])
def test_levels_grade_and_never_gate(p, name):
    assert level(p) == name


def test_describe_reads_as_a_graded_number():
    assert describe(0.83) == "83% (warn)"


def _case(runs):
    return {"id": "c", "type": "T", "algorithm": "A", "provider": "P", "operation": "OP",
            "metrics": {"timeNs": {"runs": runs}}}


def test_per_process_files_restore_the_process_index(tmp_path):
    merged, parts = tmp_path / "benchmark.json", [tmp_path / "p1.json", tmp_path / "p2.json"]
    merged.write_text(json.dumps({"cases": [_case([1, 2, 3, 10, 11, 12])]}))
    parts[0].write_text(json.dumps({"cases": [_case([1, 2, 3])]}))
    parts[1].write_text(json.dumps({"cases": [_case([10, 11, 12])]}))
    _, m, _ = read_results(merged, {}, parts)
    assert m["c"]["timeNs"].processes == ((1, 2, 3), (10, 11, 12)) and m["c"]["timeNs"].n == 6
    parts[1].write_text(json.dumps({"cases": [_case([10, 11])]}))
    with pytest.raises(ValueError, match="not the 6 runs"):
        read_results(merged, {}, parts)
