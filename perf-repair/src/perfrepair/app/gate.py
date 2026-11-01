"""The app root gate: an existing, readable Android project directory, no symlink out of it, under the size caps."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .sources import IGNORED_DIRS, SOURCE_SUFFIXES

REASONS = ("not_a_directory", "not_readable", "not_android_project", "escapes_root", "too_large")
PROJECT_FILES = ("settings.gradle", "settings.gradle.kts", "build.gradle", "build.gradle.kts")
MANIFEST = "AndroidManifest.xml"
SOURCE_SET_DIRS = ("java", "kotlin")
MAX_FILES = 200_000
MAX_SOURCE_BYTES = 256 * 2**20


class GateError(Exception):
    def __init__(self, reason: str, detail: str):
        super().__init__(f"{reason}: {detail}")
        self.reason = reason


@dataclass(frozen=True)
class AppRoot:
    path: Path
    files: int
    sourceBytes: int


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
        return True
    except ValueError:
        return False


def _source_set(rel: Path) -> bool:
    parts = rel.parts
    return len(parts) >= 3 and parts[-3] == "src" and parts[-1] in SOURCE_SET_DIRS


def open_app(root: Path, max_files: int = MAX_FILES, max_source_bytes: int = MAX_SOURCE_BYTES) -> AppRoot:
    root = Path(root)
    if not root.is_dir():
        raise GateError("not_a_directory", str(root))
    if not os.access(root, os.R_OK | os.X_OK):
        raise GateError("not_readable", str(root))
    real = root.resolve()
    if not any((root / f).is_file() for f in PROJECT_FILES):
        raise GateError("not_android_project", f"{root}: no settings.gradle(.kts) or build.gradle(.kts)")
    files = source_bytes = 0
    android = False
    for here, dirs, names in os.walk(root):
        here_path = Path(here)
        dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS)
        for name in [*dirs, *names]:
            path = here_path / name
            if path.is_symlink() and not _inside(path, real):
                raise GateError("escapes_root", f"{path.relative_to(root)} → {os.readlink(path)}")
        dirs[:] = [d for d in dirs if not (here_path / d).is_symlink()]
        android = android or MANIFEST in names or _source_set(here_path.relative_to(root))
        files += len(names)
        source_bytes += sum((here_path / n).lstat().st_size for n in names if n.endswith(SOURCE_SUFFIXES))
        if files > max_files or source_bytes > max_source_bytes:
            raise GateError("too_large", f"{root}: over {max_files} files or {max_source_bytes} source bytes")
    if not android:
        raise GateError("not_android_project", f"{root}: no {MANIFEST} and no src/*/java|kotlin source set")
    return AppRoot(real, files, source_bytes)
