import random

from cryptobench.shared.stats import inference


def draws(rng, kind, n):
    return [rng.gauss(0, 1) if kind == "normal" else rng.expovariate(1.0) for _ in range(n)]


def test_shapiro_wilk_rejects_normal_samples_at_about_alpha_and_skewed_ones_almost_always():
    rng = random.Random(1)
    normal = sum(inference.shapiro_wilk(draws(rng, "normal", 36))[1] < inference.ALPHA for _ in range(400)) / 400
    skewed = sum(inference.shapiro_wilk(draws(rng, "exponential", 36))[1] < inference.ALPHA for _ in range(200)) / 200
    assert 0.02 <= normal <= 0.09 and skewed > 0.9


def test_shapiro_wilk_has_no_answer_without_spread_or_with_too_few_values():
    assert inference.shapiro_wilk([5.0] * 10) is None and inference.shapiro_wilk([1.0, 2.0]) is None


def test_the_qq_score_is_one_on_a_straight_line_and_lower_for_a_skewed_sample():
    assert abs(inference.qq_score([3 + 2 * z for z in inference.normal_scores(40)]) - 1) < 1e-12
    assert inference.qq_score([2.0 ** i for i in range(40)]) < 0.8


def test_the_critical_value_at_50_agrees_with_the_nist_ppcc_table():
    assert abs(inference.qq_critical(50) - 0.9761) < 0.002
    assert inference.qq_critical(20) < inference.qq_critical(50) < inference.qq_critical(100)


def test_a_normal_sample_of_50_passes_in_most_seeds_and_a_lognormal_one_fails():
    def passes(seed, draw):
        rng = random.Random(seed)
        return inference.qq_test([draw(rng) for _ in range(50)])[2]
    normal = [passes(s, lambda rng: rng.gauss(0, 1)) for s in range(200)]
    lognormal = [passes(s, lambda rng: rng.lognormvariate(0, 1)) for s in range(200)]
    assert sum(normal) / 200 >= 0.9 and sum(lognormal) / 200 <= 0.1


def test_below_eight_values_the_qq_test_has_no_verdict():
    assert inference.qq_test([1.0, 2.0, 4.0, 3.0, 9.0, 5.0, 6.0]) is None
    assert inference.qq_test([1.0, 2.0, 4.0, 3.0, 9.0, 5.0, 6.0, 7.0]) is not None


def test_mann_whitney_tells_a_shift_apart_and_not_a_copy():
    rng = random.Random(2)
    a = [rng.gauss(100, 1) for _ in range(36)]
    assert inference.mann_whitney(a, [v + 5 for v in a])[1] < 1e-6
    u, p = inference.mann_whitney(a, list(a))
    assert u == 36 * 36 / 2 and p == 1.0


def test_cliffs_delta_counts_pairs_and_takes_romano_labels():
    assert inference.cliffs_delta([1, 2, 3], [4, 5, 6]) == (1.0, "large")
    assert inference.cliffs_delta([4, 5, 6], [1, 2, 3]) == (-1.0, "large")
    assert inference.cliffs_delta([1, 2, 3], [1, 2, 3]) == (0.0, "negligible")
    assert [inference.cliffs_delta([0] * 1000, [1] * k + [0] * (1000 - k))[1] for k in (146, 200, 400, 500)] == \
        ["negligible", "small", "medium", "large"]


def test_the_ratio_interval_holds_a_known_ratio_and_repeats_under_its_seed():
    rng = random.Random(3)
    base = [rng.gauss(1000, 10) for _ in range(36)]
    other = [v * 1.3 for v in base]
    ratio, low, high = inference.ratio_of_medians(base, other, resamples=2000)
    assert abs(ratio - 1.3) < 1e-12 and low < 1.3 < high
    assert inference.ratio_of_medians(base, other, resamples=2000) == (ratio, low, high)
    assert inference.ratio_of_medians(base, other, resamples=2000, seed=9) != (ratio, low, high)


def test_drift_compares_the_first_and_last_thirds_in_order():
    rng = random.Random(4)
    ramp = [100 * (1 + 0.3 * i / 99) + rng.gauss(0, 0.5) for i in range(100)]
    ratio, p = inference.drift(ramp)
    assert ratio > 1.15 and p < 1e-6
    flat = [rng.gauss(100, 1) for _ in range(100)]
    assert abs(inference.drift(flat)[0] - 1) < 0.01
    assert inference.drift([1.0] * 5) is None

