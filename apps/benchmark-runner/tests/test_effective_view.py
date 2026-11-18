import contextlib
import io
import pathlib
import tempfile
import unittest

from cryptobench.shared.settings import effective_view  # noqa: E402
from cryptobench.stages.measurement.session import passes, warmup  # noqa: E402
from failure import reported  # noqa: E402


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
        self.assertEqual(["TIME", "ALLOCATION"], effective_view.metrics({"run": {"metrics": ["TIME", "ALLOCATION"]}}))
        with self.assertRaises(SystemExit), reported():
            effective_view.metrics({"run": {}})

    def test_a_missing_key_fails_with_its_code_not_a_key_error(self):
        reads = {
            "run.processRepetitions": lambda: effective_view.process_repetitions({}),
            "run.resumeBlockRuns": lambda: effective_view.resume_block_runs({"run": {}}),
            "run.caseCooldownSeconds": lambda: effective_view.case_cooldown({"run": {}}),
            "run.warmup.iterations": lambda: warmup.settings({"run": {"warmup": {"jobs": []}}}),
            "run.warmup.jobs": lambda: warmup.settings({"run": {"warmup": {"iterations": 1}}}),
            "run.metrics": lambda: passes.read({"run": {}}, {"none"}),
        }
        for path, read in reads.items():
            stderr = io.StringIO()
            with self.subTest(path), contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit), reported():
                read()
            self.assertEqual(f"error: missing_field: {path} in effective.yaml\n", stderr.getvalue())

    def test_blocks_of_fewer_than_one_run_are_refused_as_kotlin_refuses_them(self):
        self.assertEqual(10, effective_view.resume_block_runs({"run": {"resumeBlockRuns": 10}}))
        for runs in (0, -1, 1.5, True):
            stderr = io.StringIO()
            with self.subTest(runs), contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit), reported():
                effective_view.resume_block_runs({"run": {"resumeBlockRuns": runs}})
            self.assertEqual(f"error: not_positive: run.resumeBlockRuns {runs}\n", stderr.getvalue())

    def test_an_order_seed_is_optional_and_a_hand_edited_one_not_whole_is_refused(self):
        self.assertIsNone(effective_view.order_seed({"run": {}}))
        self.assertEqual(-3, effective_view.order_seed({"run": {"orderSeed": -3}}))
        for seed in (1.5, "7", True):
            stderr = io.StringIO()
            with self.subTest(seed), contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit), reported():
                effective_view.order_seed({"run": {"orderSeed": seed}})
            self.assertEqual(f"error: invalid: run.orderSeed {seed!r}, expected a whole number\n", stderr.getvalue())

    def test_an_empty_warmup_job_list_is_read_as_written(self):
        self.assertEqual((0, []), warmup.settings({"run": {"warmup": {"iterations": 0, "jobs": []}}}))


if __name__ == "__main__":
    unittest.main()
