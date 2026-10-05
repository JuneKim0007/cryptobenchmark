import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import stats  # noqa: E402

FIXTURE = json.load(open(pathlib.Path(__file__).with_name("fixture_device_runs.json")))


class JetpackAgreement(unittest.TestCase):
    """Two real device cases, with the statistics Jetpack itself wrote: ours must not disagree."""

    def test_cov_median_min_max_match_jetpack(self):
        for case in FIXTURE:
            summary = stats.summarize(case["runs"])
            jetpack = case["jetpack"]
            self.assertAlmostEqual(summary["cov"], jetpack["coefficientOfVariation"], places=12, msg=case["case"])
            self.assertAlmostEqual(summary["median"], jetpack["median"], places=9, msg=case["case"])
            self.assertEqual(50, summary["n"])


class Definitions(unittest.TestCase):

    def test_quantile_interpolates_between_ranks(self):
        self.assertEqual(2.5, stats.quantile([1, 2, 3, 4], 50))
        self.assertEqual(1.75, stats.quantile([1, 2, 3, 4], 25))
        self.assertEqual(3.25, stats.quantile([1, 2, 3, 4], 75))

    def test_one_run_has_no_spread(self):
        summary = stats.summarize([7.0])
        self.assertEqual((0.0, 0.0, 0.0), (summary["sd"], summary["cov"], summary["iqr"]))

    def test_qcd_is_the_iqr_over_the_quartile_sum(self):
        summary = stats.summarize([1, 2, 3, 4])
        self.assertAlmostEqual((3.25 - 1.75) / (3.25 + 1.75), summary["qcd"])


class Headline(unittest.TestCase):

    def test_auto_leads_with_the_mean_while_cov_is_within_the_limit(self):
        calm = stats.summarize([100.0, 101.0, 99.0, 100.0, 100.0])
        self.assertLessEqual(calm["cov"], 0.05)
        self.assertEqual("mean", stats.headline(calm, "auto", 5.0))
        self.assertEqual("median", stats.headline(calm, "auto", 0.001))

    def test_a_few_outliers_push_auto_to_the_median(self):
        noisy = stats.summarize([100.0] * 47 + [160.0, 170.0, 180.0])
        self.assertGreater(noisy["cov"], 0.05)
        self.assertEqual("median", stats.headline(noisy, "auto", 5.0))

    def test_a_fixed_mode_ignores_the_cov(self):
        noisy = stats.summarize([1.0, 50.0, 1.0, 60.0])
        self.assertEqual("mean", stats.headline(noisy, "mean"))
        self.assertEqual("median", stats.headline(stats.summarize([1.0, 1.0, 1.0]), "median"))

    def test_the_spread_follows_the_statistic(self):
        summary = stats.summarize([1, 2, 3, 4])
        self.assertEqual(summary["sd"], stats.spread(summary, "mean"))
        self.assertEqual(summary["iqr"], stats.spread(summary, "median"))

    def test_an_unknown_mode_is_refused(self):
        with self.assertRaises(ValueError):
            stats.headline(stats.summarize([1, 2]), "average")


if __name__ == "__main__":
    unittest.main()
