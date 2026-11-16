"""attach(): perf-repair's commands attach the shared event log under the perfrepair logger, with its views."""
from __future__ import annotations

from pathlib import Path

from cryptobench.shared.log.attach import attach as attach_log
from .views import VIEWS

ROOT = "perfrepair"


def attach(device_results: Path | None = None) -> None:
    attach_log(ROOT, VIEWS, device_results)
