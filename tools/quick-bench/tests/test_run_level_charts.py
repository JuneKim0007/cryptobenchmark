import contextlib
import io
import pathlib
import sys
import tempfile
import unittest

import yaml

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import analyze  # noqa: E402

FIXTURE, PREPARED = HERE / "fixture_benchmark.json", HERE / "fixture_prepared.yaml"


class RunLevelCharts(unittest.TestCase):

    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp())

    def effective(self, analysis):
        path = self.dir / "effective.yaml"
        path.write_text(yaml.safe_dump({"runId": "r", "analysis": analysis}))
        return str(path)

    def names(self, written):
        return sorted(p.name for p in written)

    def test_all_three_are_drawn_when_the_config_says_nothing(self):
        _, _, written = analyze.build(FIXTURE, self.dir / "out", "", PREPARED)
        self.assertEqual(["latency.png", "stability.png", "throughput.png"], self.names(written))

    def test_only_the_charts_the_config_names_are_drawn(self):
        _, _, written = analyze.build(FIXTURE, self.dir / "out", self.effective({"charts": ["stability", "iqrBars"]}), PREPARED)
        self.assertEqual(["stability.png"], self.names(written))
        _, _, none = analyze.build(FIXTURE, self.dir / "out2", self.effective({"charts": []}), PREPARED)
        self.assertEqual([], none)

    def test_the_cov_limit_is_the_configured_one_not_a_literal_five(self):
        calm, _, _ = analyze.build(FIXTURE, self.dir / "a", self.effective({"statistic": {"meanUpToCovPercent": 100}}), PREPARED)
        strict, cfg, _ = analyze.build(FIXTURE, self.dir / "b", self.effective({"statistic": {"meanUpToCovPercent": 0.0001}}), PREPARED)
        self.assertEqual(0, sum(c["noisy"] for c in calm))
        self.assertEqual(len(strict), sum(c["noisy"] for c in strict))
        self.assertEqual(0.0001, cfg["limit"])

    def test_cases_without_a_group_are_reported_not_hidden(self):
        captured = io.StringIO()
        with contextlib.redirect_stderr(captured):
            analyze.build(FIXTURE, self.dir / "c", "", "")
        self.assertIn("without a chartGroup", captured.getvalue())

    def test_the_statistics_are_the_shared_ones(self):
        cases, _, _ = analyze.build(FIXTURE, self.dir / "d", "", PREPARED)
        first = cases[0]
        self.assertAlmostEqual(first["ns"]["cov"], first["ns"]["sd"] / first["ns"]["mean"])   # sample sd / mean, not pstdev / median


if __name__ == "__main__":
    unittest.main()
