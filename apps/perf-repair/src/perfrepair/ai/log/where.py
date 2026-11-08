from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Where:
    """Which stage and step a job's attempts belong to, and the app folder when it has one."""
    stage: str
    step: str
    app: str | None = None
