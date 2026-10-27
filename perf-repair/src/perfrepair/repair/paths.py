from __future__ import annotations

from pathlib import Path

DIRECTORY = "apps"


class AppPaths:
    """Files of one app under `<run>/apps/<app>/`; `original/` and `patched/` hold only the files an edit changed."""

    def __init__(self, run: Path, app: str):
        self.app = app
        self.root = Path(run) / DIRECTORY / app

    scopes = property(lambda self: self.root / "scopes.json")
    replacements = property(lambda self: self.root / "replacements.json")
    edits = property(lambda self: self.root / "edits.json")
    original = property(lambda self: self.root / "original")
    patched = property(lambda self: self.root / "patched")
    harness = property(lambda self: self.root / "harness.yaml")
    extracts = property(lambda self: self.root / "harness")
