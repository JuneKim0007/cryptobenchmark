import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import gradle_runner  # noqa: E402


class FailureMessage(unittest.TestCase):

    def test_the_tools_own_error_lines_and_their_indented_detail_are_kept(self):
        output = ["> Task :run", "error: missing_file: x.yaml", "  at global.yaml", "unrelated", "FAILURE: Build failed", "BUILD FAILED in 2s"]
        self.assertEqual("missing_file: x.yaml\n  at global.yaml", gradle_runner.failure_message(output))

    def test_without_one_the_last_lines_that_are_not_gradle_boilerplate_are_shown(self):
        output = ["a", "b", "FAILURE: Build failed", "* What went wrong", "boom", "* Try:", "BUILD FAILED"]
        self.assertEqual("a\nb\nboom", gradle_runner.failure_message(output))

    def test_a_long_message_is_cut(self):
        self.assertEqual(2000, len(gradle_runner.failure_message(["error: " + "x" * 5000])))


if __name__ == "__main__":
    unittest.main()
