"""The gate's and the run count's calculations, each rule on its own."""
import pytest

from cryptobench.measure.equations import (
    CLEAN, HOT, IGNORED, StartMargin, StartMarginRule, first_margin, half_width, median_interval, next_margin, runs_needed, start_limit,
)

RULE = StartMarginRule(initial=0.25, factor=2, maximum=3.0, clean_runs=10, recovery=0.05)


def after(margin, *outcomes):
    for outcome in outcomes:
        margin = next_margin(margin, outcome, RULE)
    return margin


def test_the_first_limit_is_the_kept_temperature_less_the_initial_margin():
    assert start_limit(36.0, first_margin(RULE)) == 35.75


@pytest.mark.parametrize("hot_runs, expected", [(1, 0.5), (2, 1.0), (3, 2.0), (4, 3.0), (5, 3.0)])
def test_a_hot_run_doubles_the_margin_up_to_the_maximum(hot_runs, expected):
    assert after(first_margin(RULE), *[HOT] * hot_runs).celsius == expected


def test_a_hot_run_ends_a_clean_streak():
    assert after(StartMargin(1.0, clean_streak=9), HOT).clean_streak == 0


def test_ten_clean_runs_in_a_row_narrow_it_by_the_recovery():
    margin = StartMargin(1.0)
    assert after(margin, *[CLEAN] * 9) == StartMargin(1.0, clean_streak=9)
    assert after(margin, *[CLEAN] * 10) == StartMargin(0.95)


def test_the_margin_never_goes_below_the_initial_so_the_limit_never_reaches_the_kept_temperature():
    margin = after(first_margin(RULE), *[CLEAN] * 500)
    assert margin.celsius == 0.25 and start_limit(36.0, margin) < 36.0


def test_an_ignored_outcome_changes_nothing():
    margin = StartMargin(1.0, clean_streak=4)
    assert next_margin(margin, IGNORED, RULE) == margin


def test_a_replayed_session_settles_and_recovers():
    margin = after(first_margin(RULE), HOT, HOT, *[CLEAN] * 10, HOT, *[CLEAN] * 20)
    assert margin.celsius == 1.8


def test_the_median_interval_uses_the_published_ranks():
    # n=9: ranks floor((9-1.96*3)/2)=1 and ceil(1+(9+1.96*3)/2)=9
    assert median_interval(list(range(1, 10))) == (1, 5, 9)


def test_the_interval_stays_inside_the_data_when_n_is_small():
    assert median_interval([2.0, 4.0]) == (2.0, 3.0, 4.0)


def test_a_split_distribution_gets_a_wide_interval():
    assert half_width([1000.0] * 12 + [1300.0] * 12) > 0.1


def test_quiet_values_need_the_fewest_listed_runs():
    assert runs_needed([1000.0 + i * 0.01 for i in range(50)], 0.02) == 5


def test_values_that_cannot_reach_the_target_say_so():
    assert runs_needed([1000.0, 1300.0] * 20, 0.02) is None


def test_the_same_values_and_seed_give_the_same_count():
    values = [1000.0 + (i * 37) % 80 for i in range(50)]
    assert runs_needed(values, 0.02, seed=7) == runs_needed(values, 0.02, seed=7)
