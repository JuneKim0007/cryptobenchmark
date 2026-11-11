"""InputError: the one coded error a refused input raises."""
from __future__ import annotations

from pathlib import Path

from .coded import Coded, code_in


class InputError(ValueError, Coded):
    """`.code` is the code the message starts with, None when it has none."""

    def __init__(self, message: str, path: Path | str | None = None, detail: str | None = None):
        super().__init__(message)
        self.code, self.path, self.detail = code_in(message), path, detail
