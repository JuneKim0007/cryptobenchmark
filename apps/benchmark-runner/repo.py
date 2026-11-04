"""The repository root every runner module resolves its paths against, the benchmark's Gradle root and the runner's own folder."""
import pathlib

RUNNER = pathlib.Path(__file__).resolve().parent
ROOT = RUNNER.parents[1]
BENCHMARK = ROOT / "apps/benchmark"
