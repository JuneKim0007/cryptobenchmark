"""A results root: the device folders it holds."""
from __future__ import annotations

from pathlib import Path

from .names import MANIFEST
from .run_tree import RunTree


class Results:

    def __init__(self, root: Path | str):
        self.root = Path(root)

    def device(self, device_id: str) -> RunTree:
        return RunTree(self.root / device_id)

    def devices(self) -> list[str]:
        """The finished devices: a folder without a manifest is a run that did not end."""
        return sorted(p.name for p in self.root.iterdir() if (p / MANIFEST).is_file()) if self.root.is_dir() else []
