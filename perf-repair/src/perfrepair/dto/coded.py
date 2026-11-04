"""The code word a failure message starts with, and InputError: the one coded error a refused input raises."""
from __future__ import annotations

import re
from pathlib import Path

# a code holds an underscore, or is one word before a colon: prose such as "pipeline exited 1" is none
CODE = re.compile(r"^(?:([a-z][a-z0-9]*_[a-z0-9_]+)\b|([a-z]+):)")


def code_in(text: str) -> str | None:
    found = CODE.match((text or "").strip())
    return (found.group(1) or found.group(2)) if found else None


class InputError(ValueError):
    """`.code` is the code the message starts with, None when it has none, so code_of reads what it always read."""

    def __init__(self, message: str, path: Path | str | None = None, detail: str | None = None):
        super().__init__(message)
        self.code, self.path, self.detail = code_in(message), path, detail
