"""A results root: the device folders it holds; finished, the one test of a run that reached its end."""
from __future__ import annotations

import re
from pathlib import Path

from .names import SESSIONS
from .run_tree import RunTree

PARTIAL = re.compile(r"^partial:", re.M)


def finished(folder: Path | str) -> bool:
    """A manifest not marked partial: a stopped run writes one with partial:, a killed one none."""
    manifest = RunTree(folder).manifest
    return manifest.is_file() and not PARTIAL.search(manifest.read_text())


class Results:

    def __init__(self, root: Path | str):
        self.root = Path(root)

    def device(self, device_id: str) -> RunTree:
        return RunTree(self.root / device_id)

    def session(self, name: str) -> Path:
        """A session's own folder: its log, summary, index and generated configs; never measurements."""
        return self.root / SESSIONS / name

    def devices(self) -> list[str]:
        """The finished devices."""
        return sorted(p.name for p in self.root.iterdir() if finished(p)) if self.root.is_dir() else []
