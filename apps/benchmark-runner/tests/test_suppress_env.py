import os, pathlib, subprocess, sys

PIPELINE = pathlib.Path(__file__).resolve().parents[1] / "pipeline.py"


def test_the_variable_counts_as_the_flag():
    env = {**os.environ, "CRYPTOBENCH_SUPPRESS_ERRORS": "EMULATOR"}
    done = subprocess.run([sys.executable, str(PIPELINE), "--bench"], env=env, capture_output=True, text=True)
    assert (done.returncode, done.stderr) == (1, "error: --suppress-errors: only a --device run reaches androidx.benchmark\n")
