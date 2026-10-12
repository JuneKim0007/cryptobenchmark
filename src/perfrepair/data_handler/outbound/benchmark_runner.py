from __future__ import annotations

import os
import subprocess
import sys
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

PIPELINE = Path("scripts/pipeline.py")
MANIFEST = "manifest.yaml"
LOG = "pipeline.log"
STAGES = {"configure": [], "bench": ["--bench"], "device": ["--device"]}
PERF_REPAIR_ROOT = Path(__file__).resolve().parents[4]


class BenchmarkRunError(RuntimeError):
    pass


def benchmark_root(explicit: Path | str | None = None) -> Path:
    root = Path(explicit or os.environ.get("CRYPTOBENCH_ROOT") or PERF_REPAIR_ROOT.parent / "cryptobenchmark")
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


def run_pipeline(config: Path, results: Path, stage: str = "configure", benchmark: Path | str | None = None,
                 extra_args: list[str] | None = None, echo: Callable[[str], None] | None = print,
                 tail: int = 40) -> Path:
    if stage not in STAGES:
        raise ValueError(f"stage {stage!r} is not one of {tuple(STAGES)}")
    root = benchmark_root(benchmark)
    results = Path(results).resolve()
    results.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(root / PIPELINE), "--config", str(Path(config).resolve()),
               "--results", str(results), *STAGES[stage], *(extra_args or [])]
    last: deque[str] = deque(maxlen=tail)
    with open(results / LOG, "w") as log, subprocess.Popen(
            command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
            env={**os.environ, "PYTHONUNBUFFERED": "1"}) as process:
        log.write("$ " + " ".join(command) + "\n")
        for line in process.stdout:
            log.write(line)
            last.append(line.rstrip("\n"))
            if echo:
                echo(line.rstrip("\n"))
        code = process.wait()
    if code != 0:
        raise BenchmarkRunError(f"pipeline exited {code} ({stage}); full log {results / LOG}; last lines:\n"
                                + "\n".join(last))
    manifest = results / MANIFEST
    if not manifest.is_file():
        raise BenchmarkRunError(f"pipeline exited 0 but wrote no {manifest}; full log {results / LOG}")
    return manifest
