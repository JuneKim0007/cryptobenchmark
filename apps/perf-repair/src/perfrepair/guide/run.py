"""Running the guide's steps: one status line and one event per step; the first that stops ends its sequence."""
from __future__ import annotations

import time
from dataclasses import dataclass

from ..ai.runtime.agent.reply import AgentFailed
from ..dto.event import END
from ..failure import FAILURES
from ..log import attach, emit
from ..log.emit import elapsed_ms
from ..result.primitives import NotScreened
from ..stop import CODES, Halt, code_of, halt_of
from .app_steps import APP_DEVICE, APP_DRY
from .state import Guide


@dataclass(frozen=True)
class Stopped:
    """halts: the provider failed, so every later app would fail the same way."""
    step: str
    code: str
    detail: str
    halts: bool = False


def _failed(g: Guide, name: str, e: Exception) -> Stopped:
    """Any other coded failure is `<step>_failed`, its own code kept as the inner one."""
    # the generic next helps nobody once the screen has scrolled: a cause on the list names the list
    named = f"read {g.missing.path}; {CODES[e.code].next}" if isinstance(e, NotScreened) and g.missing.path else None
    h = halt_of(f"{name}_failed", str(e), stage="guide", step=name, app=g.app_id, inner=code_of(e), next_step=named)
    return Stopped(name, h.code, h.detail, isinstance(e, AgentFailed))


def run_step(g: Guide, name: str, step) -> Stopped | None:
    started, stopped, detail = time.monotonic(), None, ""
    g.step = name
    if g.record is not None and g.app_id:
        g.record.app_step(g.app_id, name)
    try:
        detail = step(g)
    except Halt as e:
        stopped = Stopped(name, e.code, e.detail)
    except FAILURES as e:
        stopped = _failed(g, name, e)
    # prerequisites names the device folder when probe_device made it
    if g.device is not None:
        attach(g.device)
    outcome = "stop" if stopped else "ok"
    detail = f"{stopped.code}: {stopped.detail}" if stopped else detail
    emit("guide", name, END, app=g.app_id, outcome=outcome, durationMs=elapsed_ms(started), detail=detail,
         data={"code": stopped.code, "reported": True} if stopped else {})
    g.echo(f"guide {name}: {outcome}" + (f" {detail}" if stopped else f": {detail}"))
    return stopped


def run_sequence(g: Guide, steps: tuple) -> Stopped | None:
    for name, step in steps:
        stopped = run_step(g, name, step)
        if stopped:
            return stopped
    return None


def run_app(g: Guide, device: bool) -> Stopped | None:
    """One app's steps; the device-level ones have run."""
    stopped = run_sequence(g, APP_DRY + (APP_DEVICE if device else ()))
    if not stopped and not device:
        g.echo(f"guide: dry run ends at the harness; measure with --device, or run "
               f"`python3 apps/benchmark-runner/pipeline.py --device --harness {g.paths.harness}`")
    return stopped
