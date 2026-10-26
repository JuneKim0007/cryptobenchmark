import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import device_args  # noqa: E402


class DeviceArgs(unittest.TestCase):

    def test_time_and_allocation_need_no_launch_argument(self):
        self.assertEqual({}, device_args.arguments({"run": {"metrics": ["TIME", "ALLOCATION"]}}))

    def test_cpu_events_are_a_whole_run_switch(self):
        self.assertEqual({"androidx.benchmark.cpuEventCounter.enable": "true"},
                         device_args.arguments({"run": {"metrics": ["TIME", "CPU_EVENTS"]}}))

    def test_a_file_that_says_nothing_asks_for_time_only(self):
        self.assertEqual({}, device_args.arguments({}))

    def test_iterations_are_never_a_launch_argument(self):
        """androidx.benchmark.iterations would override every case's own count, so it is not offered."""
        args = device_args.arguments({"run": {"metrics": ["CPU_EVENTS"], "harness": {"iterations": 50}}})
        self.assertNotIn("androidx.benchmark.iterations", args)


if __name__ == "__main__":
    unittest.main()
