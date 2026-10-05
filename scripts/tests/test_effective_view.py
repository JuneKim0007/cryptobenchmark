import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import effective_view  # noqa: E402


class EffectiveView(unittest.TestCase):

    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp())
        self.effective = self.dir / "effective.yaml"

    def test_what_the_run_noticed_is_joined_back_from_the_report(self):
        self.effective.write_text("run: {processRepetitions: 3}\nproviders: {P: {Cipher: {AES: {}, DES: {}}}}\n")
        (self.dir / "report.yaml").write_text("warnings: [typo]\nskipped: [{reason: no_match}]\n")
        view = effective_view.read(self.effective)
        self.assertEqual((["typo"], [{"reason": "no_match"}]), (view["warnings"], view["skipped"]))
        self.assertEqual(2, effective_view.entry_count(view["document"]))
        self.assertEqual(3, effective_view.process_repetitions(view["document"]))

    def test_an_older_effective_file_that_holds_them_inline_is_still_read(self):
        self.effective.write_text("warnings: [old]\nskipped: [{reason: r}]\nproviders: {}\n")
        view = effective_view.read(self.effective)
        self.assertEqual((["old"], 1), (view["warnings"], len(view["skipped"])))

    def test_repetitions_default_to_one_and_must_be_positive(self):
        self.assertEqual(1, effective_view.process_repetitions({}))
        with self.assertRaises(SystemExit):
            effective_view.process_repetitions({"run": {"processRepetitions": 0}})


if __name__ == "__main__":
    unittest.main()
