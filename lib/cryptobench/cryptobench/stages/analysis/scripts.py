"""The analysis scripts over a measured benchmark.json, each a subprocess by path; a failed one is a warning and ends the rest."""
import subprocess, sys, time

from cryptobench.pipeline.took import elapsed
from cryptobench.shared import paths
from cryptobench.shared.device import timeouts
from cryptobench.shared.errors.line import one_line


def analyse(results, files, effective, preparation, benchmark, written, repetitions):
    print(f"wrote:     {paths.Measurement(benchmark).json}")
    files["benchmark"] = paths.Measurement(benchmark).json
    if repetitions > 1:
        files["processes"] = written
    started = time.monotonic()
    data, prepared = str(paths.Measurement(benchmark).json), str(paths.Preparation(preparation).prepared)
    # charts only show a benchmark already paid for: a failure warns, the first ends them, and the run keeps its files
    analysis = str(paths.RunTree(results).analysis.root)
    failed = (drawing_failed("analysis/analyze.py", data, analysis, str(effective), prepared)
              or drawing_failed("analysis/run_counts.py", analysis, *map(str, written if repetitions > 1 else [data]))
              or drawing_failed("analysis/charts.py", data, prepared, str(effective), str(results)))
    if failed:
        print(f"warning: charts_failed: {failed}")
    elapsed("analyse", started)


def drawing_failed(script, *arguments):
    """The reason this analysis script failed, else None; what it says on stderr still reaches the run's output."""
    try:
        done = timeouts.run("analysis", [sys.executable, str(paths.repo().runner / script), *arguments], stderr=subprocess.PIPE, text=True, check=False)
    except timeouts.StepTimeout as error:
        return one_line(error)
    if done.returncode == 0:
        if done.stderr:
            print(done.stderr, end="", file=sys.stderr)
        return None
    last = done.stderr.strip().splitlines()[-1:] or [f"exit {done.returncode}"]
    return one_line(f"{script}: {last[0]}")
