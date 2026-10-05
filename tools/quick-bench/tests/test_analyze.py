"""Characterisation test for analyze.py and the summary charts.py writes.

analyze.py had no tests, and every grouping, filter, threshold and derived quantity in it was a
literal. This pins what the rewritten, config-driven pair writes: analyze.py's three charts, and
the summary table charts.py writes from the same statistics (stats.py).

It is a characterisation test, not a specification. The first version pinned CoV as pstdev/median
and p90 by nearest-rank-below; both were changed on purpose to Jetpack's definitions (sample sd /
mean, interpolated quantiles), and the golden diff of that commit shows it. When one of these is
deliberately changed again, update the golden with -u and read the diff — that diff is the point.

    python3 tools/quick-bench/tests/test_analyze.py        # check
    python3 tools/quick-bench/tests/test_analyze.py -u     # accept the current output as golden

The charts are checked for existence and non-trivial size only. Comparing PNG bytes would pin the
matplotlib version rather than this project's behaviour.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ANALYZE = HERE.parent / "analyze.py"
CHARTS_PY = HERE.parent / "charts.py"
FIXTURE = HERE / "fixture_benchmark.json"
PREPARED = HERE / "fixture_prepared.yaml"
GOLDEN = HERE / "golden_summary.md"
CHARTS = ("throughput.png", "latency.png", "stability.png")


def run_analyze(into: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ANALYZE), str(FIXTURE), str(into), "", str(PREPARED)],
        capture_output=True, text=True,
    )


def run_charts(results: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CHARTS_PY), str(FIXTURE), str(PREPARED), "", str(results)],
        capture_output=True, text=True,
    )


def failures(update: bool) -> list:
    problems = []
    with tempfile.TemporaryDirectory() as temporary:
        into = pathlib.Path(temporary)
        result = run_analyze(into)
        if result.returncode != 0:
            return ["analyze.py exited {}:\n{}".format(result.returncode, result.stderr[-2000:])]

        produced_by = run_charts(into / "results")
        if produced_by.returncode != 0:
            return ["charts.py exited {}:\n{}".format(produced_by.returncode, produced_by.stderr[-2000:])]
        written = into / "results" / "chart" / "adhoc" / "summary.md"
        if not written.is_file():
            return ["charts.py wrote no summary.md"]
        produced = written.read_text()

        if update:
            GOLDEN.write_text(produced)
            print("updated", GOLDEN)
        elif not GOLDEN.is_file():
            problems.append("no golden yet; rerun with -u to accept the current output")
        elif produced != GOLDEN.read_text():
            expected = GOLDEN.read_text().splitlines()
            actual = produced.splitlines()
            diff = [
                "  line {}:\n    golden: {}\n    actual: {}".format(n + 1, e, a)
                for n, (e, a) in enumerate(zip(expected, actual)) if e != a
            ]
            if len(expected) != len(actual):
                diff.append("  line count: golden {}, actual {}".format(len(expected), len(actual)))
            problems.append("summary.md changed:\n" + "\n".join(diff[:10]))

        for chart in CHARTS:
            drawn = into / chart
            if not drawn.is_file():
                problems.append("{} was not written".format(chart))
            elif drawn.stat().st_size < 5000:
                problems.append("{} is {} bytes, too small to be a real chart".format(chart, drawn.stat().st_size))

        # The stdout line is the only machine-readable signal the script emits.
        if "cases=" not in result.stdout:
            problems.append("stdout did not report a case count:\n" + result.stdout[:500])

    return problems


def fixture_shape() -> list:
    """The fixture must keep exercising every chart, or the golden stops protecting them."""
    document = json.loads(FIXTURE.read_text())
    cases = document["cases"]
    problems = []
    for field in ("runtime", "cases"):
        if field not in document:
            problems.append("fixture lost its {} block".format(field))
    operations = {case["operation"] for case in cases}
    for needed in ("ENCRYPT", "DIGEST", "COMPUTE_MAC", "SIGN"):
        if needed not in operations:
            problems.append("fixture no longer covers {}, so a chart path is untested".format(needed))
    if not any(case["inputSize"] and case["operation"] == "ENCRYPT" for case in cases):
        problems.append("fixture has no sized ENCRYPT case, so throughput is untested")
    if not any(len(case["nanosPerOperation"]) > 1 for case in cases):
        problems.append("fixture has no multi-run case, so CoV is untested")
    return problems


def main() -> int:
    update = "-u" in sys.argv or "--update" in sys.argv
    problems = fixture_shape() + failures(update)
    if problems:
        print("FAIL")
        for problem in problems:
            print(" -", problem)
        return 1
    print("ok: analyze.py output matches the golden, {} cases".format(len(json.loads(FIXTURE.read_text())["cases"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
