"""The one warn-or-stop decision for a coded device finding: one event, outcome stop or warn, data {code, items}."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from ..dto.bundled import STOP, WARN
from ..dto.event import END
from ..log import emit


class DeviceHalt(Exception):
    """A stop before the benchmark; folder: the device folder it concerns, so the guide attaches its log there."""

    def __init__(self, code: str, detail: str, folder: Path):
        self.code, self.detail, self.folder = code, detail, Path(folder)
        super().__init__(f"{code}: {detail}")


def act(code: str, detail: str, items: list[str], on_missing: str, folder: Path, echo: Callable[[str], None]) -> None:
    outcome = STOP if on_missing == STOP else WARN
    emit("device", code, END, outcome=outcome, detail=detail, data={"code": code, "items": items})
    if outcome == STOP:
        raise DeviceHalt(code, detail, folder)
    echo(f"device {code}: {WARN}: {detail}")
