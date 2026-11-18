"""pipeline.py --session: the plan, then order groups in ascending order, one worker per target and suite (sequential until parallel lands); a
skip or failure ends only its own run and is logged in the session log, the target log and the summary; a stop reaches the running worker."""
from __future__ import annotations

import datetime
import os
import re
import sys
import time
from pathlib import Path
from typing import Callable

from cryptobench.pipeline.orchestrator import index
from cryptobench.pipeline.orchestrator import plan as session_plan
from cryptobench.pipeline.orchestrator import suite_config
from cryptobench.pipeline.orchestrator.board import StatusBoard
from cryptobench.pipeline.orchestrator.summary import Row, table, written
from cryptobench.pipeline.orchestrator.worker import COMPLETE, SERIAL, Worker
from cryptobench.shared import paths
from cryptobench.shared.device import probe
from cryptobench.shared.document.append import append_line
from cryptobench.shared.errors.failures import CommandError
from cryptobench.shared.log.warn import warn
from cryptobench.shared.results.lock import DeviceLock
from cryptobench.shared.session import targets as session_targets
from cryptobench.shared.session.targets import TargetSpec

POLL_SECONDS = 1.0
# a stopped worker gets this long to write its partial manifest before its group is killed
STOP_GRACE_SECONDS = 120
UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def folder_name(target: str) -> str:
    """A target name as a folder name on every host: emulator:cb-api33 -> emulator-cb-api33."""
    return UNSAFE.sub("-", target)


def pipeline_command(target: TargetSpec, config: Path, results: Path, passed: list[str]) -> list[str]:
    mode = "--bench" if target.transport is None else "--device"
    return [sys.executable, str(paths.repo().root / paths.PIPELINE), "--config", str(config), "--results", str(results), "--per-suite", mode, *passed]


class Session:
    """The session folder's log and the target logs; each line stamped, one coded line per skip or failure."""

    def __init__(self, folder: Path, name: str):
        self.folder, self.name = folder, name

    def log(self, line: str, target: str | None = None, suite: str | None = None) -> None:
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        append_line(self.folder / paths.SESSION_LOG, f"{stamp} {line}")
        if target is not None:
            append_line(self.target_log(target, suite), f"{stamp} session: {line}")

    def target_log(self, target: str, suite: str | None) -> Path:
        return self.folder / folder_name(target) / f"{suite or 'target'}.log"

    def config(self, target: str, suite: str) -> Path:
        return self.folder / folder_name(target) / f"{suite}.global.yaml"


def run_session(session_file: Path, results: Path, config: Callable[[], Path], passed: list[str],
                command: Callable[[TargetSpec, Path, Path, list[str]], list[str]] = pipeline_command, board: StatusBoard | None = None) -> list[Row]:
    """passed: the run options every worker gets; command builds a worker's argv (tests pass fake workers)."""
    session, rows, known, resolved = session_plan.resolved(session_file, config)
    for line in probe.listing(rows, known) + session_plan.lines(session, resolved, results):
        print(line)
    folder = paths.Results(results).session(session.name)
    with DeviceLock.take(folder):
        return orchestrated(session, resolved, Session(folder, session.name), results, passed, command, board or StatusBoard())


def orchestrated(session, resolved, log: Session, results, passed, command, board) -> list[Row]:
    log.log(f"session {session.name}: {session.path}")
    if SERIAL in os.environ:
        notice(log, f"android_serial_ignored: {SERIAL} is set; each device target gets its own serial")
    for line in session_plan.notices(resolved):
        notice(log, line)
    summary = []
    for name, line in resolved.skipped:
        print(f"skipped:   {name}: {line}")
        log.log(f"skipped: {name}: {line}", name)
        summary.append(Row(name, "-", "skipped", line.split(":", 1)[0]))
    stop = session_targets.nothing_to_measure(resolved)
    if stop:
        finish(log, summary)
        raise stop
    pending = [(target, suite) for group in session_targets.groups(resolved.targets) for target in group for suite in target.suites]
    while pending:
        target, suite = pending.pop(0)
        row = ran(target, suite, log, results, passed, command, board)
        summary.append(row)
        if row.state == "stopped":
            summary += [Row(t.name, s.stem, "not started") for t, s in pending]
            finish(log, summary, board)
            raise KeyboardInterrupt
    finish(log, summary, board)
    unfinished = [row for row in summary if row.state not in COMPLETE]
    if unfinished:
        raise CommandError(f"session_incomplete: {len(unfinished)} of {len(summary)} rows did not finish; "
                           f"see {log.folder / paths.SESSION_SUMMARY}")
    return summary


def notice(log: Session, line: str) -> None:
    warn(line)
    log.log(f"notice: {line}")


def ran(target: TargetSpec, suite: Path, log: Session, results: Path, passed, command, board) -> Row:
    """One suite on one target; its config generated, its worker started, watched and its outcome logged."""
    config = suite_config.written(target.config, suite, log.config(target.name, suite.stem))
    worker = Worker(command(target, config, results, passed), target.transport, log.target_log(target.name, suite.stem))
    label = f"{target.name} {suite.stem}"
    log.log(f"start: {label}: {' '.join(worker.command)}", target.name, suite.stem)
    worker.start()
    try:
        while worker.poll() is None:
            board.update(target.name, f"{suite.stem}: {worker.last_line() or 'started'}")
            time.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        worker.stop()
        deadline = time.monotonic() + STOP_GRACE_SECONDS
        try:
            while worker.poll() is None and time.monotonic() < deadline:
                time.sleep(POLL_SECONDS)
        except KeyboardInterrupt:
            pass
        if worker.poll() is None:
            worker.kill()
            worker.process.wait()
    outcome = worker.outcome()
    status = outcome.state if outcome.line is None else f"{outcome.state}: {outcome.line}"
    board.update(target.name, f"{suite.stem}: {status}")
    log.log(f"{outcome.state}: {label}: {outcome.line or outcome.results or ''}".rstrip(": "), target.name, suite.stem)
    return Row(target.name, suite.stem, outcome.state, outcome.code, outcome.results)


def finish(log: Session, summary: list[Row], board: StatusBoard | None = None) -> None:
    if board:
        board.done()
    path = written(summary, log.folder / paths.SESSION_SUMMARY)
    print(f"summary:   {path}")
    for line in table(summary):
        print(f"  {line}")
    log.log(f"summary: {path}")
    listed = index.written(log.name, summary, log.folder / paths.INDEX)
    print(f"index:     {listed}")
    log.log(f"index: {listed}")
