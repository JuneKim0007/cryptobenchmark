"""Guide: the settings every step reads and the step running; halt and check_exit, a step's coded stop."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .. import run_dir as rd
from ..ai.runtime.agent import Conversations
from ..ai.runtime.engine.ask import Limits
from ..ai.runtime.prompt import PromptLibrary
from ..app.facts.path_id import path_id
from ..app.facts.target_set import TargetSet
from ..config.load import Loaded
from ..device.primitives_missing import MissingList
from ..dto.bundled import BundledPolicy
from ..dto.change import DROP_IN
from ..failure import last_failure
from ..result.modes import Mode
from ..run_dir.run_record import OVERWRITE, RunRecord
from ..screen.catalog import Catalog
from ..stop import terminate


@dataclass
class Guide:
    """device: the named device folder; with root instead, prerequisites makes it by probe_device() and sets it.
    app_root: None for the device-level steps, which run once before the apps."""
    device: Path | None
    app_root: Path | None
    mode: Mode
    conversations: Conversations
    library: PromptLibrary
    limits: Limits = Limits()
    limit: int | None = None
    config: Path | None = None
    # the per-app device step; None uses config
    app_config: Path | None = None
    # the global.yaml probe_device resolved when config is unset, for the per-app device step
    base_config: Path | None = None
    settings: Loaded | None = None
    echo: Callable[[str], None] = print
    catalog: Catalog | None = None
    root: Path | None = None
    on_device: bool = False
    grouping_args: tuple[str, ...] = ()
    refresh: bool = False
    targets: tuple[Path, ...] = ()
    # the command sets it from device.filterByApps
    filter_by_apps: bool = False
    # the command sets it from device.bundled
    bundled: BundledPolicy = BundledPolicy()
    # app ids whose app step ran before the benchmark, shared by every app's copy
    detected: set = field(default_factory=set)
    max_change: str = DROP_IN
    # the targets that name their own perfMode, by root; the others take mode
    app_modes: dict = field(default_factory=dict)
    # apps.targets resolved (app/facts/target_set.py); None with --app
    target_set: TargetSet | None = None
    # the running step's name, set by run_step, so a stop's line says where
    step: str | None = None
    # --run-id (None: a timestamp) and --on-existing; the record opens once the device folder is known
    run_id: str | None = None
    on_existing: str = OVERWRITE
    record: RunRecord | None = None
    # units the replace step left unasked under apps.limit
    unasked: int = 0
    # shared by every app's copy: what this run found unavailable
    missing: MissingList = field(default_factory=MissingList)
    stop_after_device: bool = False
    # the facade's settings tree and digests, kept in the record
    run_settings: dict | None = None
    # the code of the device step or the first app that stopped, for --outcome
    stop_code: str | None = None

    @property
    def app_id(self) -> str | None:
        return path_id(self.app_root) if self.app_root else None

    @property
    def paths(self) -> rd.AppPaths:
        return rd.AppPaths(self.device, self.app_id)


def halt(g: Guide, code: str, detail: str, inner: str | None = None) -> None:
    terminate(code, detail, stage="guide", step=g.step or "guide", app=g.app_id, inner=inner)


def check_exit(g: Guide, code: int, stop: str, what: str) -> None:
    """A command run in-process wrote no error event: its coded failure is the inner code of this one line; its Halt
    already has its line and goes on as it is."""
    if code != 0:
        inner = last_failure()
        if inner and inner.halt:
            raise inner.halt
        said = f": {inner.detail}" if inner and inner.detail else "; its own lines above say why"
        halt(g, stop, f"{what} exited {code}" + said, inner.code if inner else None)
