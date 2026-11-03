"""An item's fixed and notFixed rows stay two rows in every table and two series in every chart, never one."""
import json
import pathlib
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import analyze  # noqa: E402
import chart_draw  # noqa: E402
import chart_model  # noqa: E402

FIXTURE = HERE / "fixture_benchmark.json"


class Variants(unittest.TestCase):

    def split(self):
        document = json.loads(FIXTURE.read_text())
        case = next(c for c in document["cases"] if c["type"] == "MessageDigest")
        twins = [dict(case, id=f"{case['id']}_{v}", variant=v) for v in ("fixed", "notFixed")]
        document["cases"] = twins
        path = pathlib.Path(tempfile.mkdtemp()) / "benchmark.json"
        path.write_text(json.dumps(document))
        return path, case

    def test_the_summary_names_each_variant_on_its_own_row(self):
        path, case = self.split()
        out = path.parent / "out"
        analyze.build(path, out)
        lines = [line for line in (out / "summary.md").read_text().splitlines() if line.startswith(f"| {case['algorithm']} ")]
        self.assertEqual([f"{case['operation']} fixed", f"{case['operation']} notFixed"], [line.split(" | ")[1] for line in lines])

    def test_the_series_label_differs_per_variant_and_a_row_without_one_keeps_its_old_label(self):
        row = {"algorithm": "SHA-256", "keySize": None}
        self.assertEqual(["SHA-256 fixed", "SHA-256 notFixed", "SHA-256"],
                         [chart_draw.label(dict(row, variant=v)) for v in ("fixed", "notFixed", None)])
        self.assertEqual("", chart_model.variant({}))


if __name__ == "__main__":
    unittest.main()
