import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import explain  # noqa: E402

GLOBAL = "schemaVersion: 1\nselection: {testSet: t.yaml}\nrun:\n  seed: 7\n  harness: {iterations: 50}\n"
EFFECTIVE = """schemaVersion: 1
generatedFrom: {global: g.yaml, testSet: t.yaml}
runId: 20261005T103349Z
run:
  inputSizes: [1024]
  seed: 7
  harness: {iterations: 50}
policy: {onFailure: skip}
analysis:
  statistic: {headline: auto, meanUpToCovPercent: 5.0}
  charts: [iqrBars]
providers:
  SunJCE:
    Cipher:
      AES: {}
"""


class Explain(unittest.TestCase):

    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp())
        (self.dir / "global.yaml").write_text(GLOBAL)
        (self.dir / "effective.yaml").write_text(EFFECTIVE)

    def rows(self):
        rows, entries, testset, run_id = explain.explain(self.dir / "global.yaml", self.dir / "effective.yaml")
        return {dotted: (value, source) for dotted, value, source in rows}, entries, testset, run_id

    def test_a_key_the_file_spells_out_is_that_files_and_the_rest_are_defaults(self):
        rows, entries, testset, run_id = self.rows()
        self.assertEqual((7, "global.yaml"), rows["run.seed"])
        self.assertEqual((50, "global.yaml"), rows["run.harness.iterations"])
        self.assertEqual(([1024], "default"), rows["run.inputSizes"])
        self.assertEqual(("skip", "default"), rows["policy.onFailure"])
        self.assertEqual((1, "t.yaml", "20261005T103349Z"), (entries, testset, run_id))

    def test_an_authored_default_is_still_reported_as_authored(self):
        (self.dir / "global.yaml").write_text(GLOBAL + "policy: {onFailure: skip}\n")
        self.assertEqual(("skip", "global.yaml"), self.rows()[0]["policy.onFailure"])

    def test_nested_analysis_keys_are_listed(self):
        rows = self.rows()[0]
        self.assertIn("analysis.statistic.meanUpToCovPercent", rows)
        self.assertEqual(([ "iqrBars"], "default"), rows["analysis.charts"])


if __name__ == "__main__":
    unittest.main()
