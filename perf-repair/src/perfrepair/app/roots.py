"""Android project roots under a folder: a settings file, or a build file beside an Android source set or at the top."""
from __future__ import annotations

import os
from pathlib import Path

from ..source.language import NAMES
from .sources import IGNORED_DIRS

SETTINGS_FILES = ("settings.gradle", "settings.gradle.kts")
BUILD_FILES = ("build.gradle", "build.gradle.kts")
MANIFEST = "AndroidManifest.xml"
MAX_DEPTH = 4


class EscapingLink(Exception):
    def __init__(self, link: Path, target: str):
        super().__init__(f"{link} → {target}")
        self.link = link


def _has_source_set(d: Path) -> bool:
    if (d / MANIFEST).is_file():
        return True
    src = d / "src"
    return src.is_dir() and any((s / MANIFEST).is_file() or any((s / n).is_dir() for n in NAMES)
                                for s in src.iterdir() if s.is_dir())


def _is_root(d: Path, top: bool) -> bool:
    if any((d / f).is_file() for f in SETTINGS_FILES):
        return True
    # the folder itself keeps the original rule, any build file, so top-level projects scan as before
    return any((d / f).is_file() for f in BUILD_FILES) and (top or _has_source_set(d))


def project_roots(folder: Path, max_depth: int = MAX_DEPTH) -> list[str]:
    """Relative roots, outermost only: a root inside another is one of its modules; '.' is the folder itself."""
    folder = Path(folder)
    real = folder.resolve()
    found: list[str] = []
    pending = [(folder, 0)]
    while pending:
        d, depth = pending.pop()
        if _is_root(d, depth == 0):
            found.append(d.relative_to(folder).as_posix() or ".")
            continue
        if depth == max_depth:
            continue
        for child in sorted(d.iterdir(), reverse=True):
            if child.is_symlink():
                if not child.resolve().is_relative_to(real):
                    raise EscapingLink(child.relative_to(folder), os.readlink(child))
            elif child.is_dir() and child.name not in IGNORED_DIRS:
                pending.append((child, depth + 1))
    return sorted(found)
