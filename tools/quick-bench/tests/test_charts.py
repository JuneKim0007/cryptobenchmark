import json
import pathlib
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import chart_input  # noqa: E402
import charts  # noqa: E402

CALM = [100.0, 101.0, 99.0, 100.0, 100.0] * 10
NOISY = [100.0] * 47 + [160.0, 170.0, 180.0]


def case(cid, type_, algorithm, operation, key, size, runs):
    return {"id": cid, "type": type_, "algorithm": algorithm, "provider": "P", "operation": operation, "keySize": key, "inputSize": size,
            "metrics": {"timeNs": {"runs": runs}}}


class Charts(unittest.TestCase):

    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp())
        cases = [case("a64", "Cipher", "AES", "ENCRYPT", 128, 64, CALM), case("a1k", "Cipher", "AES", "ENCRYPT", 128, 1024, NOISY),
                 case("b64", "Cipher", "ChaCha20", "ENCRYPT", None, 64, CALM), case("h64", "MessageDigest", "SHA-256", "DIGEST", None, 64, CALM),
                 case("g", "KeyPairGenerator", "EC", "GENERATE-KEY-PAIR", None, None, NOISY)]
        (self.dir / "benchmark.json").write_text(json.dumps({"cases": cases}))
        groups = {"a64": (1, "symmetric-cipher"), "a1k": (1, "symmetric-cipher"), "b64": (1, "symmetric-cipher"), "h64": (4, "hash"), "g": (9, "keygen-asymmetric")}
        (self.dir / "prepared.yaml").write_text(yaml.safe_dump({"cases": [{"id": i, "chartGroupId": g[0], "chartGroup": g[1]} for i, g in groups.items()]}))
        self.write_effective({"runId": "20261005T103349Z"})

    def write_effective(self, document):
        (self.dir / "effective.yaml").write_text(yaml.safe_dump(document))

    def run_charts(self):
        return charts.build(self.dir / "benchmark.json", self.dir / "prepared.yaml", self.dir / "effective.yaml", self.dir / "results")

    def test_one_chart_per_group_operation_and_fixed_input_size(self):
        root, written = self.run_charts()
        names = sorted(str(p.relative_to(root)) for p in written)
        self.assertEqual(["1-symmetric-cipher/iqr-bars_encrypt_input-1KiB.png", "1-symmetric-cipher/iqr-bars_encrypt_input-64B.png",
                          "4-hash/iqr-bars_digest_input-64B.png", "9-keygen-asymmetric/iqr-bars_generate-key-pair_input-n-a.png"], names)
        self.assertEqual(self.dir / "results" / "chart" / "20261005T103349Z", root)

    def test_the_summary_and_data_carry_both_statistics_and_the_run_count(self):
        root, _ = self.run_charts()
        data = {c["id"]: c for c in json.load(open(root / "chart-data.json"))}
        self.assertEqual(50, data["a64"]["ns"]["n"])
        self.assertFalse(data["a64"]["noisy"])
        self.assertTrue(data["a1k"]["noisy"])
        self.assertEqual("mean", data["a64"]["lead"])
        self.assertEqual("median", data["a1k"]["lead"])
        self.assertIn("| noisy |", (root / "summary.md").read_text())
        manifest = yaml.safe_load((root / "manifest.yaml").read_text())
        self.assertEqual([50], manifest["runsPerCase"])
        self.assertEqual(2, manifest["noisy"])

    def test_throughput_is_shown_for_payload_groups_and_microseconds_otherwise(self):
        root, _ = self.run_charts()
        data = {c["id"]: c for c in json.load(open(root / "chart-data.json"))}
        self.assertEqual("MB/s", data["a64"]["unit"])
        self.assertAlmostEqual(64 / 100.0 * 1000, data["a64"]["shown"]["median"], places=6)
        self.assertEqual("us/op", data["g"]["unit"])

    def test_naming_other_charts_turns_the_bars_off_but_keeps_the_summary(self):
        self.write_effective({"runId": "r1", "analysis": {"charts": ["stability"]}})
        root, written = self.run_charts()
        self.assertEqual([], written)
        self.assertTrue((root / "summary.md").is_file())

    def test_dir_overrides_the_root_and_may_name_the_run(self):
        self.write_effective({"runId": "r2", "analysis": {"dir": str(self.dir / "out" / "<run-id>")}})
        root, _ = self.run_charts()
        self.assertEqual(self.dir / "out" / "r2", root)

    def test_a_case_missing_from_the_prepared_file_is_group_zero(self):
        (self.dir / "prepared.yaml").write_text(yaml.safe_dump({"cases": []}))
        root, written = self.run_charts()
        self.assertTrue(all("0-unidentified" in str(p) for p in written))

    def test_missing_groups_are_said_out_loud(self):
        import contextlib
        import io
        (self.dir / "prepared.yaml").write_text(yaml.safe_dump({"cases": []}))
        captured = io.StringIO()
        with contextlib.redirect_stderr(captured):
            self.run_charts()
        self.assertIn("5 of 5 cases have no chartGroup", captured.getvalue())

    def test_a_limit_from_the_config_moves_the_noisy_line(self):
        self.write_effective({"runId": "r3", "analysis": {"statistic": {"headline": "auto", "meanUpToCovPercent": 0.0001}}})
        root, _ = self.run_charts()
        data = json.load(open(root / "chart-data.json"))
        self.assertTrue(all(c["noisy"] for c in data))
 
    def test_the_python_defaults_match_the_ones_the_config_module_writes(self):
        example = pathlib.Path(__file__).resolve().parents[3] / "modules/config/example/config_effective_example.yaml"
        analysis = yaml.safe_load(example.read_text())["analysis"]
        self.assertEqual(chart_input.DEFAULTS["charts"], analysis["charts"])
        self.assertEqual(chart_input.DEFAULTS["headline"], analysis["statistic"]["headline"])
        self.assertEqual(chart_input.DEFAULTS["meanUpToCovPercent"], analysis["statistic"]["meanUpToCovPercent"])


class AuditAgainstJetpack(unittest.TestCase):
    """benchmark.json carries what androidx reported; our statistics must equal it, and a difference must be said, not smoothed over."""

    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp())
        import stats
        self.runs = [100.5, 101.25, 99.75, 100.0, 100.5, 99.5] * 8 + [100.0, 100.0]
        s = stats.summarize(self.runs)
        self.truth = {"minimum": s["min"], "maximum": s["max"], "median": s["median"], "coefficientOfVariation": s["cov"]}

    def build(self, reported):
        block = {"runs": self.runs}
        if reported is not None:
            block["reported"] = reported
        (self.dir / "benchmark.json").write_text(json.dumps({"cases": [dict(case("c", "Mac", "HmacSHA256", "COMPUTE_MAC", None, 64, self.runs), metrics={"timeNs": block})]}))
        (self.dir / "prepared.yaml").write_text(yaml.safe_dump({"cases": [{"id": "c", "chartGroupId": 5, "chartGroup": "mac"}]}))
        (self.dir / "effective.yaml").write_text(yaml.safe_dump({"runId": "r"}))
        return charts.build(self.dir / "benchmark.json", self.dir / "prepared.yaml", self.dir / "effective.yaml", self.dir / "results")[0]

    def manifest(self, root):
        return yaml.safe_load((root / "manifest.yaml").read_text())["auditAgainstJetpack"]

    def test_statistics_that_equal_the_reported_ones_pass(self):
        audit = self.manifest(self.build(self.truth))
        self.assertEqual((1, []), (audit["checked"], audit["mismatches"]))

    def test_a_difference_is_named_in_the_manifest_and_on_stderr(self):
        import contextlib
        import io
        wrong = dict(self.truth, coefficientOfVariation=self.truth["coefficientOfVariation"] * 1.01)
        captured = io.StringIO()
        with contextlib.redirect_stderr(captured):
            audit = self.manifest(self.build(wrong))
        self.assertEqual(["c"], audit["mismatches"])
        self.assertAlmostEqual(0.01 / 1.01, audit["maxRelativeDifference"]["cov"], places=9)   # relative to the reported value
        self.assertIn("disagree with the statistics androidx reported", captured.getvalue())

    def test_a_case_with_nothing_reported_is_not_audited_and_not_failed(self):
        audit = self.manifest(self.build(None))
        self.assertEqual((0, []), (audit["checked"], audit["mismatches"]))


if __name__ == "__main__":
    unittest.main()
