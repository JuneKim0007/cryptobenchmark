import pytest

from perfrepair.dto.dossier import Estimate
from perfrepair.result.gain import (IMPROVED, UNCHANGED, WORSE, by_change, change_of, label_of, noise_of, option_label,
                                    strict_passes)


def e(metric, ratio, p, n=50):
    return Estimate(metric, ratio, p, n, "OP key 128 input 64 WARM")


@pytest.mark.parametrize("ratio,p,want", [
    (0.8, 0.99, IMPROVED), (1.2, 0.01, WORSE), (0.8, 0.9, UNCHANGED), (1.2, 0.1, UNCHANGED), (0.99, 0.99, UNCHANGED),
    (1.02, 0.01, UNCHANGED), (0.5, None, UNCHANGED), (None, 0.99, UNCHANGED)])
def test_a_change_is_beyond_both_noise_and_the_improving_ratio(ratio, p, want):
    assert change_of(ratio, p) == want


def test_noise_says_whether_the_bootstrap_tells_the_sides_apart():
    assert [noise_of(p) for p in (0.99, 0.01, 0.5, None)] == ["beyond", "beyond", "within", "unknown"]


def test_one_metric_up_and_one_down_is_a_trade_off():
    both = (e("timeNs", 0.7, 0.99), e("allocationCount", 1.5, 0.01))
    assert option_label(both) == "trade_off"
    assert by_change(both, IMPROVED) == ["timeNs"] and by_change(both, WORSE) == ["allocationCount"]
    assert not strict_passes(both)


def test_the_other_labels():
    assert option_label((e("timeNs", 0.7, 0.99), e("energyJ", 1.0, None, 1))) == "improves"
    assert option_label((e("timeNs", 1.3, 0.01),)) == "worse"
    assert option_label((e("timeNs", 1.0, 0.5),)) == "unchanged"
    assert option_label(()) == label_of([]) == "not_measured"


def test_the_strict_rule_reads_the_ratio_only_as_the_verdict_does():
    assert strict_passes((e("energyJ", 0.8, None, 1),)) and not strict_passes((e("timeNs", 1.0, 0.5),))
