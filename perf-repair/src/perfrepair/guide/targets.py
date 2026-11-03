"""The guide over its apps: the device-level steps once, each app isolated, a report summary and one line per app."""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from ..dto.event import END
from ..failure import record_bug
from ..log import emit
from . import finished
from .run import Stopped, run_app, run_sequence, run_step
from .steps import DEVICE_LEVEL, Guide, summary

OK, REUSED, STOP, NOT_RUN = "ok", "reused", "stop", "not_run"


@dataclass(frozen=True)
class AppResult:
    app: str
    status: str
    detail: str = ""
    halts: bool = False

    @property
    def line(self) -> str:
        return f"app {self.app}: {self.status}" + (f" {self.detail}" if self.detail else "")


def _stopped(app: str, s: Stopped) -> AppResult:
    return AppResult(app, STOP, f"{s.code} at {s.step}: {s.detail}", s.halts)


def _attempt(g: Guide, device: bool, reuse: bool) -> AppResult:
    now = finished.inputs(g, device)
    if reuse and finished.unchanged(g, now):
        return AppResult(g.app_id, REUSED)
    stopped = run_app(g, device)
    if stopped:
        return _stopped(g.app_id, stopped)
    finished.record(g, now)
    return AppResult(g.app_id, OK)


def _one(base: Guide, root: Path, device: bool, reuse: bool) -> AppResult:
    g = replace(base, app_root=root)
    if not root.is_dir():
        return AppResult(g.app_id, STOP, f"target_missing: {root} is no folder; its earlier results stay")
    try:
        return _attempt(g, device, reuse)
    except Exception as e:
        # no step codes this: a bug in this app's handling, logged with its traceback; the others still run
        record_bug(e)
        return _stopped(g.app_id, Stopped("app", "bug", f"{type(e).__name__}: {e}"))


def _not_run(base: Guide, root: Path, halted: AppResult) -> AppResult:
    return AppResult(replace(base, app_root=root).app_id, NOT_RUN, f"{halted.app} hit a provider failure, which any app would")


def run_targets(base: Guide, roots: list[Path], device: bool, reuse: bool) -> int:
    """reuse: an app whose inputs match its record is not run again. Exit 0 only if every app reached its last step."""
    if run_sequence(base, DEVICE_LEVEL):
        return 1
    results: list[AppResult] = []
    halted = None
    for root in roots:
        result = _not_run(base, root, halted) if halted else _one(base, root, device, reuse)
        results.append(result)
        halted = halted or (result if result.halts else None)
        emit("guide", "target", END, app=result.app, outcome=result.status, detail=result.detail)
    run_step(base, "summary", summary)
    for result in results:
        base.echo(result.line)
    return 0 if all(r.status in (OK, REUSED) for r in results) else 1
