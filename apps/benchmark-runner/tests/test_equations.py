"""The run count's calculations, each rule on its own."""
import math

from cryptobench.shared.stats.equations import SUBSAMPLE_SIZES, half_width, median_ranks, rank_interval, runs_needed


def test_the_ranks_are_the_widest_binomial_tail_within_the_level():
    for n in range(6, 120):
        low, high, coverage = median_ranks(n)
        tail = lambda r: sum(math.comb(n, k) for k in range(r)) / 2 ** n
        assert high == n + 1 - low and coverage == 1 - 2 * tail(low)
        assert tail(low) <= 0.025 < tail(low + 1) and coverage >= 0.95


def test_the_ranks_match_the_published_values():
    assert median_ranks(36)[:2] == (12, 25)
    assert median_ranks(50)[:2] == (18, 33)


def test_the_rank_interval_reads_the_values_at_those_ranks():
    low, high, _ = median_ranks(9)
    assert rank_interval(list(range(1, 10))) == (low, 5, high)


def test_the_interval_stays_inside_the_data_when_n_is_small():
    assert rank_interval([2.0, 4.0]) == (2.0, 3.0, 4.0)


def test_a_split_distribution_gets_a_wide_interval():
    assert half_width([1000.0] * 12 + [1300.0] * 12) > 0.1


def test_quiet_values_need_the_fewest_listed_runs():
    assert runs_needed([1000.0 + i * 0.01 for i in range(50)], 0.02) == 5


def test_values_that_cannot_reach_the_target_say_so():
    assert runs_needed([1000.0, 1300.0] * 20, 0.02) is None


def test_fixed_values_need_the_same_listed_count_under_every_seed():
    values = [1000.0 + (i * 37) % 80 for i in range(50)]
    counts = {runs_needed(values, 0.022, seed=s) for s in range(1, 6)}
    assert len(counts) == 1 and counts <= set(SUBSAMPLE_SIZES)
    assert min(SUBSAMPLE_SIZES) < next(iter(counts)) < len(values)


def test_a_looser_target_needs_no_more_runs():
    values = [1000.0 + (i * 37) % 80 for i in range(50)]
    assert runs_needed(values, 0.05) <= runs_needed(values, 0.02) <= runs_needed(values, 0.015)
