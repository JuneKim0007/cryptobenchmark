"""--refresh: run inputs no outbox holds yet, so a charter opens a new outbox; later runs keep it by reading its inputs back."""
from __future__ import annotations

import secrets
from pathlib import Path

from ....run_dir import CHARTER
from . import charter_file
from .outbox import active_outbox

REFRESH = "refresh "


def refresh_inputs() -> str:
    return REFRESH + secrets.token_hex(6)


def kept_inputs(root: Path) -> str:
    """The active outbox's refresh inputs, so a run without --refresh stays in it; empty otherwise."""
    active = active_outbox(root)
    if active.fingerprint is None:
        return ""
    kept = charter_file.inputs(active.directory / CHARTER)
    return kept if kept.startswith(REFRESH) else ""
