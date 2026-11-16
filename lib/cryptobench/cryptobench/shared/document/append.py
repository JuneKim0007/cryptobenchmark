"""append_line: one whole line appended, a newline first when a crash cut the file's last line."""
from __future__ import annotations

import os
from pathlib import Path


def _ends_mid_line(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size == 0:
        return False
    with path.open("rb") as f:
        f.seek(-1, os.SEEK_END)
        return f.read(1) != b"\n"


def append_line(path: Path, line: str) -> bool:
    """One write of one whole line in append mode; True when the file ended mid-line (a crash cut its last line), so a
    newline went first and the cut line stays a line of its own."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    cut = _ends_mid_line(path)
    with path.open("a") as f:
        f.write(("\n" if cut else "") + line.rstrip("\n") + "\n")
    return cut
