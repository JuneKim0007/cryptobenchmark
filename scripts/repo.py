"""The repository root every script resolves its paths against, and the benchmark's Gradle root under it."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
BENCHMARK = ROOT / "apps/benchmark"
