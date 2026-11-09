"""The checkout this code is, and the checkout a run measures; two roots, because a test or the CLI may point a run at another checkout."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from ..coded import InputError

CODE_ROOT_ENV, BENCHMARK_ROOT_ENV = "CRYPTOBENCH_CODE_ROOT", "CRYPTOBENCH_ROOT"
ALGORITHMS, RUNNER, PIPELINE = "algorithms", "apps/benchmark-runner", "apps/benchmark-runner/pipeline.py"


def _is_checkout(folder: Path) -> bool:
    return (folder / ALGORITHMS).is_dir() and (folder / PIPELINE).is_file()


def _walk_up(start: Path) -> Path | None:
    start = start.resolve()
    return next((folder for folder in start.parents if _is_checkout(folder)), None)


def code_root() -> Path:
    """$CRYPTOBENCH_CODE_ROOT, else the checkout of the script that runs, else this library's own; a script of checkout B beats a library installed from A."""
    named = os.environ.get(CODE_ROOT_ENV)
    if named:
        root = Path(named).expanduser().resolve()
        if not _is_checkout(root):
            raise InputError(f"root_not_found: {root} ({CODE_ROOT_ENV}) has no {ALGORITHMS}/ and {PIPELINE}")
        return root
    script = getattr(sys.modules.get("__main__"), "__file__", None)
    for start in ((Path(script),) if script else ()) + (Path(__file__),):
        found = _walk_up(start)
        if found:
            return found
    raise InputError(f"root_not_found: no folder above {script or __file__} has {ALGORITHMS}/ and {PIPELINE}; set {CODE_ROOT_ENV}")


def benchmark_root(explicit: Path | str | None = None, error: type[Exception] = InputError) -> Path:
    """explicit, else $CRYPTOBENCH_ROOT, else this checkout; a folder without a pipeline is refused with error."""
    root = Path(explicit or os.environ.get(BENCHMARK_ROOT_ENV) or code_root())
    if not (root / PIPELINE).is_file():
        raise error(f"no {PIPELINE} under {root}: pass the benchmark root or set {BENCHMARK_ROOT_ENV}")
    return root.resolve()
