"""The start margin's calculations, each rule on its own."""
import pytest

from cryptobench.stages.measurement.start_margin import (
    CLEAN, HOT, IGNORED, StartMargin, StartMarginRule, first_margin, next_margin, start_limit,
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
