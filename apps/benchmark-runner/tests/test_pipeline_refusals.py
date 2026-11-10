"""pipeline.py's refused flag combinations as the command reports them: exit 1 and exactly one error line on stderr."""
import os, pathlib, subprocess, sys

import pytest

import pipeline

PIPELINE = pathlib.Path(__file__).resolve().parents[1] / "pipeline.py"

REFUSALS = [
    (["--probe", "--bench"], "--probe, --identify: no measuring, so neither goes with --bench, --harness or --interop"),
    (["--harness", "harness.yaml"], "--harness: scopes are checked only on a --device run"),
    (["--check", "--probe"], "--check: runs alone with --bench or --device, without --probe, --identify, --harness or --interop"),
    (["--device", "--discovery", "reuse"], "--discovery reuse: a device run probes the device it measures"),
    (["--suppress-errors", "EMULATOR"], "--suppress-errors: only a --device run reaches androidx.benchmark"),
    (["--energy-accept-unresponsive"], "--energy-accept-unresponsive: only a --device run captures energy"),
]


def command(*flags, **env):
    clean = {k: v for k, v in os.environ.items() if k != "CRYPTOBENCH_SUPPRESS_ERRORS"}
    return subprocess.run([sys.executable, str(PIPELINE), *flags], env={**clean, **env}, capture_output=True, text=True, timeout=60)


def test_the_refusal_table_has_six_rows_in_this_order():
    assert [message for _refused, message in pipeline.REFUSED] == [message for _flags, message in REFUSALS]


@pytest.mark.parametrize("flags, message", REFUSALS, ids=[" ".join(f) for f, _m in REFUSALS])
def test_a_refused_combination_exits_1_with_its_one_line(flags, message):
    done = command(*flags)
    assert (done.returncode, done.stdout, done.stderr) == (1, "", f"error: {message}\n")


def test_the_first_refusal_that_matches_is_the_one_reported():
    done = command("--probe", "--bench", "--check", "--energy-accept-unresponsive")
    assert done.stderr == f"error: {REFUSALS[0][1]}\n"


def test_bench_with_device_is_refused_by_argparse_with_exit_2():
    done = command("--bench", "--device")
    assert done.returncode == 2 and done.stdout == ""
    assert done.stderr.splitlines()[-1] == "pipeline.py: error: argument --device: not allowed with argument --bench"
