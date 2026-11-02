"""The app gate: a readable folder holding Android project roots, each with no symlink out of it, under the size caps."""
from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path

from ...source.language import NAMES, SOURCE_SUFFIXES
from .roots import BUILD_FILES, MANIFEST, MAX_DEPTH as MAX_ROOT_DEPTH, SETTINGS_FILES, EscapingLink, project_roots
from ..find.sources import IGNORED_DIRS

PROJECT_FILES = SETTINGS_FILES + BUILD_FILES
SOURCE_SET_DIRS = NAMES  # Gradle names a source set folder after its language
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
    projectRoot: str = "."


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
        return True
    except ValueError:
        return False


def _source_set(rel: Path) -> bool:
    parts = rel.parts
    return len(parts) >= 3 and parts[-3] == "src" and parts[-1] in SOURCE_SET_DIRS


def _readable_dir(root: Path) -> None:
    if not root.is_dir():
        raise GateError("not_a_directory", str(root))
    if not os.access(root, os.R_OK | os.X_OK):
        raise GateError("not_readable", str(root))


def open_apps(folder: Path, max_files: int = MAX_FILES, max_source_bytes: int = MAX_SOURCE_BYTES) -> list[AppRoot]:
    """One AppRoot per outermost Android project root under folder, in path order."""
    folder = Path(folder)
    _readable_dir(folder)
    try:
        rels = project_roots(folder)
    except EscapingLink as e:
        raise GateError("escapes_root", str(e)) from None
    if not rels:
        raise GateError("not_android_project", f"{folder}: no settings.gradle(.kts), or build.gradle(.kts) beside "
                                               f"an Android source set, within {MAX_ROOT_DEPTH} levels")
    return [replace(open_app(folder / rel, max_files, max_source_bytes), projectRoot=rel) for rel in rels]


def open_app(root: Path, max_files: int = MAX_FILES, max_source_bytes: int = MAX_SOURCE_BYTES) -> AppRoot:
    root = Path(root)
    _readable_dir(root)
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
    return AppRoot(real, files)
