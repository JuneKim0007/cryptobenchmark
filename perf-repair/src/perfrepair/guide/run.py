"""Running the guide's steps: one status line and one event per step; the first that stops ends its sequence."""
from __future__ import annotations

import time
from dataclasses import dataclass

from ..ai.runtime.agent.reply import AgentFailed
from ..dto.event import END
from ..failure import FAILURES
from ..log import attach, emit
from ..log.emit import elapsed_ms
from .steps import APP_DRY, APP_MEASURED, DEVICE_LEVEL, Guide, Stop


@dataclass(frozen=True)
class Stopped:
    """halts: the provider failed, so every later app would fail the same way."""
    step: str
    code: str
    detail: str
    halts: bool = False


def run_step(g: Guide, name: str, step) -> Stopped | None:
    started, stopped, detail = time.monotonic(), None, ""
    try:
        detail = step(g)
    except Stop as e:
        stopped = Stopped(name, e.code, e.detail)
    except FAILURES as e:
        stopped = Stopped(name, f"{name}_failed", str(e), isinstance(e, AgentFailed))
    # prerequisites names the device folder when probe_device made it
    if g.device is not None:
        attach(g.device)
    outcome = "stop" if stopped else "ok"
    detail = f"{stopped.code}: {stopped.detail}" if stopped else detail
    emit("guide", name, END, app=g.app_id, outcome=outcome, durationMs=elapsed_ms(started), detail=detail)
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
    stopped = run_sequence(g, APP_DRY + (APP_MEASURED if device else ()))
    if not stopped and not device:
        g.echo(f"guide: dry run ends at the harness; measure with --device, or run "
               f"`python3 scripts/pipeline.py --device --harness {g.paths.harness}`")
    return stopped


def run_steps(g: Guide, device: bool) -> int:
    """The device-level steps, then the one app g names."""
    return 1 if run_sequence(g, DEVICE_LEVEL) or run_app(g, device) else 0
