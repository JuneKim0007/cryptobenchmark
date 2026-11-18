import pathlib
import tempfile
import unittest

import explain  # noqa: E402

EFFECTIVE = """schemaVersion: 1
generatedFrom:
  global: g.yaml
  testSet: t.yaml
  settings: {run.seed: layer 1 global.yaml, run.harness.iterations: layer 2 overlay.yaml, run.inputSizes: default}
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
        (self.dir / "effective.yaml").write_text(EFFECTIVE)

    def rows(self):
        rows, entries, testset, run_id = explain.explain(self.dir / "effective.yaml")
        return {dotted: (value, source) for dotted, value, source in rows}, entries, testset, run_id

    def test_each_key_shows_the_layer_generated_from_names_and_the_rest_are_defaults(self):
        rows, entries, testset, run_id = self.rows()
        self.assertEqual((7, "layer 1 global.yaml"), rows["run.seed"])
        self.assertEqual((50, "layer 2 overlay.yaml"), rows["run.harness.iterations"])
        self.assertEqual(([1024], "default"), rows["run.inputSizes"])
        self.assertEqual(("skip", "default"), rows["policy.onFailure"])
        self.assertEqual((1, "t.yaml", "20261005T103349Z"), (entries, testset, run_id))

    def test_an_effective_file_without_provenance_is_refused(self):
        (self.dir / "effective.yaml").write_text(EFFECTIVE.replace("  settings:", "  other:"))
        with self.assertRaisesRegex(Exception, "missing_field: generatedFrom.settings"):
            self.rows()

if __name__ == "__main__":
    unittest.main()
