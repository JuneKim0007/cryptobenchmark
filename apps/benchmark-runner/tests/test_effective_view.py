import contextlib
import io
import pathlib
import tempfile
import unittest

import effective_view  # noqa: E402
from session import passes, warmup  # noqa: E402


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

    def test_metrics_are_read_and_their_absence_fails(self):
        self.assertEqual(["TIME", "CPU_EVENTS"], effective_view.metrics({"run": {"metrics": ["TIME", "CPU_EVENTS"]}}))
        with self.assertRaises(SystemExit):
            effective_view.metrics({"run": {}})

    def test_a_missing_key_fails_with_its_code_not_a_key_error(self):
        reads = {
            "run.isolation": lambda: effective_view.isolation({"run": {}}),
            "run.processRepetitions": lambda: effective_view.process_repetitions({}),
            "run.caseCooldownSeconds": lambda: effective_view.case_cooldown({"run": {}}),
            "run.warmup.iterations": lambda: warmup.settings({"run": {"warmup": {"jobs": []}}}),
            "run.warmup.jobs": lambda: warmup.settings({"run": {"warmup": {"iterations": 1}}}),
            "run.metrics": lambda: passes.read({"run": {}}, {"none"}),
        }
        for path, read in reads.items():
            stderr = io.StringIO()
            with self.subTest(path), contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
                read()
            self.assertEqual(f"error: missing_field: {path} in effective.yaml\n", stderr.getvalue())

    def test_an_empty_warmup_job_list_is_read_as_written(self):
        self.assertEqual((0, []), warmup.settings({"run": {"warmup": {"iterations": 0, "jobs": []}}}))


if __name__ == "__main__":
    unittest.main()
