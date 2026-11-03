from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from ...child.deadline import Deadline
from ...child.env import child_env
from ...config.timeouts import pipeline_seconds
from ...log import run_id
from ...stop import terminate
from ...run_dir import PIPELINE_LOGS

PIPELINE = Path("scripts/pipeline.py")
# the id is known only to the run, so the run says where its manifest went
WROTE_MANIFEST = re.compile(r"^wrote:\s+(.*/manifest\.yaml)$")
IDENTITY = re.compile(r"^identity:\s+(\{.*\})$")
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


def _chosen(config: Path | None) -> list[str]:
    # None: pipeline.py resolves global.yaml itself (--config, CRYPTOBENCH_CONFIG, then its defaults)
    return ["--config", str(Path(config).resolve())] if config is not None else []


def identify(config: Path | None, on_device: bool, benchmark: Path | str | None = None) -> dict:
    """pipeline.py --identify: deviceId, mode, config and input digests, before any probe; nothing is written."""
    root = benchmark_root(benchmark)
    command = [sys.executable, str(root / PIPELINE), *_chosen(config), "--identify", *(["--device"] if on_device else [])]
    seconds = pipeline_seconds()
    with subprocess.Popen(command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                          env=child_env(), start_new_session=True) as process, Deadline(process, seconds) as deadline:
        lines = process.communicate()[0].splitlines()
    if deadline.expired:
        _timed_out("identify", seconds, None, None)
    found = [m.group(1) for m in map(IDENTITY.match, lines) if m]
    if process.returncode != 0 or not found:
        raise BenchmarkRunError(f"identify_failed: pipeline --identify exited {process.returncode}; last lines:\n"
                                + "\n".join(lines[-10:]))
    return json.loads(found[-1])


def transcript(device: Path) -> Path:
    """<device>/log/pipeline/<run id>.log: every pipeline call of one run appends to it."""
    path = Path(device).resolve() / PIPELINE_LOGS / f"{run_id()}.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _lines(path: Path) -> int:
    if not path.is_file():
        return 0
    with open(path) as f:
        return sum(1 for _ in f)


def _failed(stage: str, code: int, last: list[str], ref: str, app: str | None) -> None:
    """The one line of a failed call: its exit and last error line here, its tail only in the Halt's message."""
    errors = [line for line in last if line.lstrip().startswith("error")] or [line for line in last if line.strip()]
    terminate("pipeline_failed", f"pipeline exited {code} ({stage})" + (f"; {errors[-1].strip()}" if errors else ""),
              stage="device", step="pipeline", item=stage, app=app, ref=ref, data={"exit": code, "stage": stage},
              trace=f"; full log {ref}; last lines:\n" + "\n".join(last))


def _timed_out(stage: str, seconds: int, ref: str | None, app: str | None) -> None:
    terminate("pipeline_timeout", f"pipeline ran past {seconds}s ({stage}); killed with its children",
              stage="device", step="pipeline", item=stage, app=app, ref=ref, data={"seconds": seconds, "stage": stage})


def _stream(process: subprocess.Popen, log, last: deque[str], echo: Callable[[str], None] | None) -> Path | None:
    """Every line into the transcript and the tail; the manifest the run says it wrote."""
    manifest = None
    for line in process.stdout:
        log.write(line)
        last.append(line.rstrip("\n"))
        wrote = WROTE_MANIFEST.match(last[-1])
        manifest = Path(wrote.group(1)) if wrote else manifest
        if echo:
            echo(last[-1])
    return manifest


def run_pipeline(config: Path | None, results: Path | None, stage: str = "configure",
                 benchmark: Path | str | None = None, harness: Path | None = None,
                 echo: Callable[[str], None] | None = print, tail: int = 40, extra: tuple[str, ...] = (),
                 app: str | None = None, *, device: Path) -> Path:
    """results: the root, unused with harness, where pipeline.py picks measured/ itself; device: the folder whose log/
    keeps the transcript."""
    if stage not in STAGES:
        raise ValueError(f"stage {stage!r} is not one of {tuple(STAGES)}")
    root = benchmark_root(benchmark)
    target = ["--harness", str(harness)] if harness else ["--results", str(Path(results).resolve())]
    command = [sys.executable, str(root / PIPELINE), *_chosen(config), *target, *STAGES[stage], *extra]
    log_path = transcript(device)
    # the call's first line, so a reference lands on this call among the run's others
    ref = f"{log_path}:{_lines(log_path) + 1}"
    last: deque[str] = deque(maxlen=tail)
    seconds = pipeline_seconds()
    with open(log_path, "a") as log, subprocess.Popen(
            command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
            env=child_env(PYTHONUNBUFFERED="1"), start_new_session=True) as process, Deadline(process, seconds) as deadline:
        log.write(f"# {stage}" + (f" app {app}" if app else "") + "\n$ " + " ".join(command) + "\n")
        manifest = _stream(process, log, last, echo)
        code = process.wait()
    if deadline.expired:
        _timed_out(stage, seconds, ref, app)
    if code != 0:
        _failed(stage, code, list(last), ref, app)
    if manifest is None or not manifest.is_file():
        raise BenchmarkRunError(f"pipeline exited 0 but wrote no manifest; full log {ref}")
    return manifest
