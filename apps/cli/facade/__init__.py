"""Package of apps/cli/facade.py: the settings index, the tree check, the phases. Puts the benchmark runner and perfrepair
and the shared library on the path, as all run here."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
RUNNER = ROOT / "apps/benchmark-runner"
SOURCE = ROOT / "apps/perf-repair/src"
LIBRARY = ROOT / "lib/cryptobench"
for path in (RUNNER, SOURCE, LIBRARY):
    sys.path.insert(0, str(path))
