import contextlib
import io
import pathlib
import tempfile
import unittest

from cryptobench.shared.errors.failures import CommandError  # noqa: E402
from cryptobench.shared.settings import effective_view  # noqa: E402
from cryptobench.shared.settings.effective_view import AnalysisView, GateView, RunView  # noqa: E402
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
        self.assertEqual(3, RunView(view["document"]).process_repetitions)

    def test_metrics_are_read_and_their_absence_fails(self):
        self.assertEqual(["TIME", "ALLOCATION"], RunView({"run": {"metrics": ["TIME", "ALLOCATION"]}}).metrics)
        with self.assertRaises(SystemExit), reported():
            RunView({"run": {}}).metrics

    def test_a_missing_key_fails_with_its_code_not_a_key_error(self):
        reads = {
            "run.processRepetitions": lambda: RunView({}).process_repetitions,
            "run.resumeBlockRuns": lambda: RunView({"run": {}}).resume_block_runs,
            "run.caseCooldownSeconds": lambda: RunView({"run": {}}).case_cooldown,
            "run.warmup.iterations": lambda: warmup.settings({"run": {"warmup": {"jobs": [], "cases": 3}}}),
            "run.warmup.jobs": lambda: warmup.settings({"run": {"warmup": {"iterations": 1, "cases": 3}}}),
            "run.warmup.cases": lambda: warmup.settings({"run": {"warmup": {"iterations": 1, "jobs": []}}}),
            "run.metrics": lambda: passes.read(RunView({"run": {}}), {"none"}),
        }
        for path, read in reads.items():
            stderr = io.StringIO()
            with self.subTest(path), contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit), reported():
                read()
            self.assertEqual(f"error: missing_field: {path} in effective.yaml\n", stderr.getvalue())

    def test_blocks_of_fewer_than_one_run_are_refused_as_kotlin_refuses_them(self):
        self.assertEqual(10, RunView({"run": {"resumeBlockRuns": 10}}).resume_block_runs)
        for runs in (0, -1, 1.5, True):
            stderr = io.StringIO()
            with self.subTest(runs), contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit), reported():
                RunView({"run": {"resumeBlockRuns": runs}}).resume_block_runs
            self.assertEqual(f"error: not_positive: run.resumeBlockRuns {runs}\n", stderr.getvalue())

    def test_an_order_seed_is_required_and_a_hand_edited_one_not_whole_is_refused(self):
        with self.assertRaisesRegex(CommandError, "^missing_field: run.orderSeed in effective.yaml$"):
            RunView({"run": {}}).order_seed
        self.assertEqual(-3, RunView({"run": {"orderSeed": -3}}).order_seed)
        for seed in (1.5, "7", True):
            stderr = io.StringIO()
            with self.subTest(seed), contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit), reported():
                RunView({"run": {"orderSeed": seed}}).order_seed
            self.assertEqual(f"error: invalid: run.orderSeed {seed!r}, expected a whole number\n", stderr.getvalue())

    def test_an_empty_warmup_job_list_is_read_as_written(self):
        self.assertEqual((0, [], 3), warmup.settings({"run": {"warmup": {"iterations": 0, "jobs": [], "cases": 3}}}))

    def test_every_view_field_is_a_key_row_and_an_unknown_one_is_refused(self):
        for view, field, path, _, _ in effective_view.KEYS:
            if view:
                self.assertEqual(path, effective_view.ROWS[(view, field)][0])
        self.assertEqual(36.0, GateView({"run": {"thermalGate": {"temperatureKeptCelsius": 36.0}}}).kept)
        with self.assertRaises(AttributeError):
            RunView({}).typo

    def test_analysis_falls_back_to_the_written_defaults_only_where_absent(self):
        self.assertEqual(("auto", {"latency": "us"}), (AnalysisView({}).headline, AnalysisView({"analysis": {"units": {"latency": "us"}}}).units))
        self.assertEqual({"latency": "ms", "throughput": "MB/s"}, AnalysisView({}).units)

    def test_the_host_ignores_only_the_keys_set_to_other_than_the_default(self):
        document = {"run": {"caseCooldownSeconds": 0, "launchRetries": 4, "orderSeed": 1, "warmup": {"iterations": 10, "jobs": [], "cases": 5},
                            "processRepetitions": 3, "harness": {"profiling": "none"}}}
        self.assertEqual(["run.orderSeed", "run.launchRetries", "run.warmup.cases", "run.harness.profiling"], effective_view.ignored_on_host(document))


if __name__ == "__main__":
    unittest.main()
