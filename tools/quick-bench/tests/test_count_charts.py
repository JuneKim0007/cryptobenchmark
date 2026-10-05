import json
import pathlib
import sys
import tempfile
import unittest

import yaml

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import analyze  # noqa: E402
import chart_model  # noqa: E402
import charts  # noqa: E402

TIME = [100.0, 101.0, 99.0, 100.0, 100.0] * 10          # 50 runs
ALLOC = [3.0, 3.0, 3.0, 4.0, 5.0]                        # 5 runs


def case(cid, type_, algorithm, operation, key, size, alloc=None):
    metrics = {"timeNs": {"runs": TIME}}
    if alloc is not None:
        metrics["allocationCount"] = {"iterations": 1, "runs": alloc}
    return {"id": cid, "type": type_, "algorithm": algorithm, "provider": "P", "operation": operation, "keySize": key, "inputSize": size, "metrics": metrics}


class CountCharts(unittest.TestCase):

    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp())
        groups = {"a64": (1, "symmetric-cipher"), "b64": (1, "symmetric-cipher"), "h64": (4, "hash")}
        (self.dir / "prepared.yaml").write_text(yaml.safe_dump({"cases": [{"id": i, "chartGroupId": g[0], "chartGroup": g[1]} for i, g in groups.items()]}))
        self.effective({"runId": "r"})

    def effective(self, document):
        (self.dir / "effective.yaml").write_text(yaml.safe_dump(document))

    def benchmark(self, cases):
        (self.dir / "benchmark.json").write_text(json.dumps({"cases": cases}))

    def with_alloc(self):
        self.benchmark([case("a64", "Cipher", "AES", "ENCRYPT", 128, 64, ALLOC), case("b64", "Cipher", "ChaCha20", "ENCRYPT", None, 64, [0.0] * 5),
                        case("h64", "MessageDigest", "SHA-256", "DIGEST", None, 64, ALLOC)])

    def run_charts(self):
        return charts.build(self.dir / "benchmark.json", self.dir / "prepared.yaml", self.dir / "effective.yaml", self.dir / "results")

    def test_a_time_only_run_writes_no_count_output(self):
        self.benchmark([case("a64", "Cipher", "AES", "ENCRYPT", 128, 64), case("h64", "MessageDigest", "SHA-256", "DIGEST", None, 64)])
        root, written = self.run_charts()
        self.assertEqual(["iqr-bars_digest_input-64B.png", "iqr-bars_encrypt_input-64B.png"], sorted(p.name for p in written))
        self.assertNotIn("allocation", (root / "summary.md").read_text())
        self.assertFalse(list(root.glob("chart-data-*.json")))
        self.assertNotIn("countMetrics", yaml.safe_load((root / "manifest.yaml").read_text()))

    def test_allocation_gets_median_and_min_max_bars_per_group_operation_and_size(self):
        self.with_alloc()
        root, written = self.run_charts()
        names = sorted(str(p.relative_to(root)) for p in written if "allocationCount" in p.name)
        self.assertEqual(["1-symmetric-cipher/allocationCount-bars_encrypt_input-64B.png", "4-hash/allocationCount-bars_digest_input-64B.png"], names)
        self.assertEqual(2, sum("iqr-bars" in p.name for p in written))             # the time bars are untouched

    def test_the_summary_and_data_state_n_and_the_observed_range_without_an_iqr(self):
        self.with_alloc()
        root, _ = self.run_charts()
        text = (root / "summary.md").read_text()
        self.assertIn("## allocationCount: allocations per call (n = 5 runs per case)", text)
        section = text.split("## allocationCount")[1]
        self.assertIn("| 5 | 3 | 3 | 5 | 3 3 3 4 5 |", section)
        self.assertNotIn("iqr", section.lower())
        rows = {r["id"]: r for r in json.load(open(root / "chart-data-allocationCount.json"))}
        self.assertEqual([3.0, 3.0, 3.0, 4.0, 5.0], rows["a64"]["runs"])
        self.assertEqual(0.0, rows["b64"]["stats"]["median"])
        manifest = yaml.safe_load((root / "manifest.yaml").read_text())
        self.assertEqual([5], manifest["countMetrics"]["allocationCount"]["runsPerCase"])
        self.assertEqual([50], manifest["runsPerCase"])

    def test_an_explicit_chart_list_without_countBars_turns_them_off(self):
        self.with_alloc()
        self.effective({"runId": "r", "analysis": {"charts": ["iqrBars"]}})
        _, written = self.run_charts()
        self.assertFalse([p for p in written if "allocationCount" in p.name])

    def test_a_metric_with_no_runs_is_not_a_metric(self):
        raw = [case("a64", "Cipher", "AES", "ENCRYPT", 128, 64, []), case("h64", "MessageDigest", "SHA-256", "DIGEST", None, 64, ALLOC)]
        self.assertEqual(["allocationCount"], chart_model.count_metrics(raw))
        self.assertIsNone(chart_model.summarize_count(raw[0], {}, "allocationCount"))
        self.assertEqual([], chart_model.count_metrics([raw[0]]))

    def test_any_other_metric_is_charted_the_same_way_under_its_own_name(self):
        raw = case("a64", "Cipher", "AES", "ENCRYPT", 128, 64)
        raw["metrics"]["instructions"] = {"runs": [1000.0, 1100.0, 900.0]}
        self.benchmark([raw])
        _, written = self.run_charts()
        self.assertEqual(["instructions-bars_encrypt_input-64B.png"], [p.name for p in written if "instructions" in p.name])

    def test_allocation_against_time_is_a_run_level_chart_only_when_allocation_exists(self):
        self.with_alloc()
        _, _, written = analyze.build(self.dir / "benchmark.json", self.dir / "out", "", self.dir / "prepared.yaml")
        self.assertIn("allocationCount-vs-time.png", sorted(p.name for p in written))
        self.benchmark([case("a64", "Cipher", "AES", "ENCRYPT", 128, 64)])
        _, _, none = analyze.build(self.dir / "benchmark.json", self.dir / "out2", "", self.dir / "prepared.yaml")
        self.assertNotIn("allocationCount-vs-time.png", sorted(p.name for p in none))


if __name__ == "__main__":
    unittest.main()
