"""The guide over its apps: the device-level steps once, each app isolated, a report summary and one line per app."""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from ..device.missing_rows import measured_rows, site_rows
from ..dto.event import END
from ..failure import record_bug
from ..log import emit
from ..run_dir.run_record import FAILED, STOPPED
from ..stop import halt_of
from . import finished
from .device_steps import DEVICE_LEVEL, DEVICE_STAGE, summary
from .run import Stopped, run_app, run_sequence, run_step
from .state import Guide
from .target_file import refused

OK, REUSED, STOP, NOT_RUN = "ok", "reused", "stop", "not_run"
# the pipeline reached an answer for the app: done, and an unchanged rerun skips it
TERMINAL = ("no_options", "no_replacement")


@dataclass(frozen=True)
class AppResult:
    app: str
    status: str
    detail: str = ""
    halts: bool = False
    code: str | None = None
    step: str | None = None
    interrupted: bool = False

    @property
    def line(self) -> str:
        return f"app {self.app}: {self.status}" + (f" {self.detail}" if self.detail else "")


def _stopped(app: str, s: Stopped) -> AppResult:
    return AppResult(app, STOP, f"{s.code} at {s.step}: {s.detail}", s.halts, s.code, s.step)


def _reused(g: Guide) -> AppResult:
    # a reused app's sites still stand, and this run's list starts empty
    g.missing.put(f"sites {g.app_id}", site_rows(g.device, g.app_id))
    g.missing.put(f"measured {g.app_id}", measured_rows(g.device, g.app_id))
    outcome = g.record.app_reused(g.app_id)
    return AppResult(g.app_id, REUSED, f"({outcome})" if outcome not in ("", OK) else "")


def _attempt(g: Guide, device: bool, reuse: bool) -> AppResult:
    # --refresh asks stale scopes again, which a reused app would never reach
    if reuse and not g.refresh and g.record.is_done(g.app_id, finished.inputs(g, device)):
        return _reused(g)
    stopped = run_app(g, device)
    if g.unasked:
        g.record.app_failed(g.app_id, "replace", f"apps.limit left {g.unasked} scopes unasked", STOPPED)
    elif stopped is None or stopped.code in TERMINAL:
        # read again: the run wrote the scopes it ended with
        g.record.app_done(g.app_id, finished.inputs(g, device), stopped.code if stopped else OK)
    else:
        g.record.app_failed(g.app_id, stopped.step, f"{stopped.code}: {stopped.detail}")
    return _stopped(g.app_id, stopped) if stopped else AppResult(g.app_id, OK)


def _missing(g: Guide, root: Path) -> AppResult:
    h = halt_of("target_missing", f"{root} is no folder; its earlier results stay", stage="guide", step="target",
                app=g.app_id)
    return AppResult(g.app_id, STOP, str(h), code=h.code)


def _one(base: Guide, root: Path, device: bool, reuse: bool) -> AppResult:
    g = replace(base, app_root=root, mode=base.app_modes.get(root, base.mode), step=None, unasked=0)
    if not root.is_dir():
        return _missing(g, root)
    try:
        return _attempt(g, device, reuse)
    except KeyboardInterrupt:
        g.record.app_failed(g.app_id, g.step or "app", "interrupted", STOPPED)
        return AppResult(g.app_id, STOP, f"interrupted at {g.step or 'app'}", step=g.step, interrupted=True)
    except Exception as e:
        # no step codes this: a bug in this app's handling, logged with its traceback; the others still run
        record_bug(e)
        stopped = Stopped(g.step or "app", "bug", f"{type(e).__name__}: {e}")
        g.record.app_failed(g.app_id, stopped.step, f"bug: {stopped.detail}")
        return _stopped(g.app_id, stopped)


def _not_run(base: Guide, root: Path, halted: AppResult) -> AppResult:
    return AppResult(replace(base, app_root=root).app_id, NOT_RUN, f"{halted.app} hit a provider failure, which any app would")


def _refused(base: Guide) -> list[AppResult]:
    """Each path entry that is no app, as its stop; a root's skipped candidates are no app's result."""
    results = []
    for s in base.target_set.skipped if base.target_set else ():
        if s.stops:
            app, h = refused(s)
            results.append(AppResult(app, STOP, str(h), code=h.code))
            _emit(results[-1])
    return results


def _emit(result: AppResult) -> None:
    # a stopped app's line is the one its terminate or bug event wrote
    emit("guide", "target", END, app=result.app, outcome=result.status, detail=result.detail,
         data={k: v for k, v in (("code", result.code), ("step", result.step), ("reported", result.status == STOP)) if v})


def _device_stage(base: Guide) -> bool:
    """The device-level steps and their record; True when one stopped."""
    try:
        stopped = run_sequence(base, DEVICE_STAGE if base.stop_after_device else DEVICE_LEVEL)
    except KeyboardInterrupt:
        if base.record is not None:
            base.record.device_done(STOPPED, base.step, "interrupted")
        raise
    if base.record is not None:
        base.record.device_done(*((FAILED, stopped.step, f"{stopped.code}: {stopped.detail}") if stopped else ()))
    base.stop_code = stopped.code if stopped else None
    return stopped is not None


def run_targets(base: Guide, roots: list[Path], device: bool, reuse: bool) -> int:
    """reuse: an app whose inputs match its record is not run again. Exit 0 only if every app reached its last step.
    Ctrl-C ends the loop at that app; the summary, index and its line are still written, then it is raised again."""
    try:
        return _targets(base, roots, device, reuse)
    finally:
        if base.record is not None:
            base.record.close()


def _targets(base: Guide, roots: list[Path], device: bool, reuse: bool) -> int:
    if _device_stage(base):
        return 1
    if base.stop_after_device:
        return 0
    results = _refused(base)
    halted = None
    for root in roots:
        result = _not_run(base, root, halted) if halted else _one(base, root, device, reuse)
        results.append(result)
        halted = halted or (result if result.halts else None)
        _emit(result)
        if result.interrupted:
            break
    run_step(base, "summary", summary)
    base.stop_code = next((r.code for r in results if r.code), None)
    for result in results:
        base.echo(result.line)
    if any(r.interrupted for r in results):
        raise KeyboardInterrupt
    return 0 if all(r.status in (OK, REUSED) for r in results) else 1
