from __future__ import annotations

from ...validation.repair import EDIT_REASONS


class Rejected(Exception):
    """An edit that cannot be applied exactly; `reason` is one of EDIT_REASONS and lands in edits.json."""

    def __init__(self, reason: str):
        if reason not in EDIT_REASONS:
            raise ValueError(f"{reason}: not an edit reason")
        super().__init__(reason)
        self.reason = reason
