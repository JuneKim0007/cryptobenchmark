from __future__ import annotations

import os
import re
import subprocess
import sys
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

PIPELINE = Path("scripts/pipeline.py")
# the id is known only to the run, so the run says where its manifest went
WROTE_MANIFEST = re.compile(r"^wrote:\s+(.*/manifest\.yaml)$")
LOG = "pipeline.log"
STAGES = {"configure": [], "bench": ["--bench"], "device": ["--device"]}
PERF_REPAIR_ROOT = Path(__file__).resolve().parents[4]


class BenchmarkRunError(RuntimeError):
    pass


def benchmark_root(explicit: Path | str | None = None) -> Path:
    root = Path(explicit or os.environ.get("CRYPTOBENCH_ROOT") or PERF_REPAIR_ROOT.parent)
    if not (root / PIPELINE).is_file():
        raise BenchmarkRunError(f"no {PIPELINE} under {root}: pass the benchmark root or set CRYPTOBENCH_ROOT")
    return root.resolve()


def new_run_dir(root: Path | str) -> Path:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for n in range(1000):
        candidate = root / (stamp if n == 0 else f"{stamp}-{n}")
        try:
            candidate.mkdir()
            return candidate
        except FileExistsError:
            continue
    raise BenchmarkRunError(f"could not create a run directory under {root}")


def run_pipeline(config: Path | None, results: Path, stage: str = "configure", benchmark: Path | str | None = None,
                 harness: Path | None = None, echo: Callable[[str], None] | None = print, tail: int = 40) -> Path:
    """results: the root, or with harness the folder beside it that only holds the log; pipeline.py picks measured/ itself."""
    if stage not in STAGES:
        raise ValueError(f"stage {stage!r} is not one of {tuple(STAGES)}")
    root = benchmark_root(benchmark)
    results = Path(results).resolve()
    results.mkdir(parents=True, exist_ok=True)
    # config None: pipeline.py resolves global.yaml itself (--config, CRYPTOBENCH_CONFIG, then its defaults)
    chosen = ["--config", str(Path(config).resolve())] if config is not None else []
    target = ["--harness", str(harness)] if harness else ["--results", str(results)]
    command = [sys.executable, str(root / PIPELINE), *chosen, *target, *STAGES[stage]]
    last: deque[str] = deque(maxlen=tail)
    manifest = None
    with open(results / LOG, "w") as log, subprocess.Popen(
            command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
            env={**os.environ, "PYTHONUNBUFFERED": "1"}) as process:
        log.write("$ " + " ".join(command) + "\n")
        for line in process.stdout:
            log.write(line)
            last.append(line.rstrip("\n"))
            wrote = WROTE_MANIFEST.match(last[-1])
            manifest = Path(wrote.group(1)) if wrote else manifest
            if echo:
                echo(line.rstrip("\n"))
        code = process.wait()
    if code != 0:
        raise BenchmarkRunError(f"pipeline exited {code} ({stage}); full log {results / LOG}; last lines:\n"
                                + "\n".join(last))
    if manifest is None or not manifest.is_file():
        raise BenchmarkRunError(f"pipeline exited 0 but wrote no manifest; full log {results / LOG}")
    return manifest
