"""The run count's calculations, each rule on its own."""
from cryptobench.shared.stats.equations import half_width, rank_interval, runs_needed


def test_the_rank_interval_uses_the_published_ranks():
    # n=9: ranks floor((9-1.96*3)/2)=1 and ceil(1+(9+1.96*3)/2)=9
    assert rank_interval(list(range(1, 10))) == (1, 5, 9)


def test_the_interval_stays_inside_the_data_when_n_is_small():
    assert rank_interval([2.0, 4.0]) == (2.0, 3.0, 4.0)


def test_a_split_distribution_gets_a_wide_interval():
    assert half_width([1000.0] * 12 + [1300.0] * 12) > 0.1


def test_quiet_values_need_the_fewest_listed_runs():
    assert runs_needed([1000.0 + i * 0.01 for i in range(50)], 0.02) == 5


def test_values_that_cannot_reach_the_target_say_so():
    assert runs_needed([1000.0, 1300.0] * 20, 0.02) is None


def test_fixed_values_need_the_same_count_under_two_seeds():
    values = [1000.0 + (i * 37) % 80 for i in range(50)]
    assert {runs_needed(values, 0.02, seed=s) for s in (7, 8)} == {30}
