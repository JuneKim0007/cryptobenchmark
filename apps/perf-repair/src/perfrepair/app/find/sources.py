"""An app tree's source and build files; each source file tagged main, test or generated."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from cryptobench.shared import paths
from cryptobench.shared.document.document import read_yaml
from ...config import current
from ...inputs.table import APPS_COPIES
from ...source.language import SOURCE_SUFFIXES, Language, of_file

BUILD_NAMES = ("build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts", "gradle.properties")
CATALOG = "libs.versions.toml"
TOOLING_DIRS = frozenset(read_yaml(paths.IGNORED_FILES.path)["tooling"])
MAIN, TEST, GENERATED = "main", "test", "generated"

_TEST_SET = re.compile(r"^(test|androidTest)|Test$")


@dataclass(frozen=True)
class SourceFile:
    path: Path
    rel: str
    origin: str

    @property
    def language(self) -> Language:
        return of_file(self.path.name)


def copy_dirs() -> frozenset[str]:
    return frozenset(current.read(APPS_COPIES))


def ignored_dirs() -> frozenset[str]:
    return TOOLING_DIRS | copy_dirs()


def walk(root: Path):
    """Every regular file under root, ignored folders pruned, symlinks not followed, in a stable order."""
    ignored = ignored_dirs()
    for here, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in ignored and not os.path.islink(os.path.join(here, d)))
        for name in sorted(files):
            path = Path(here) / name
            if not path.is_symlink():
                yield path


def skipped_copies(root: Path) -> int:
    """Stale copies the scan did not enter, each counted once; nothing under an ignored folder is looked at."""
    count, copies = 0, copy_dirs()
    ignored = TOOLING_DIRS | copies
    for _, dirs, _ in os.walk(root):
        count += sum(d in copies for d in dirs)
        dirs[:] = [d for d in dirs if d not in ignored]
    return count


def origin(rel: Path) -> str:
    parts = rel.parts
    if any(p.startswith("generated") for p in parts[:-1]):
        return GENERATED
    for i, p in enumerate(parts[:-1]):
        if p == "src" and i + 1 < len(parts) - 1 and _TEST_SET.search(parts[i + 1]):
            return TEST
    return MAIN


def source_files(root: Path) -> list[SourceFile]:
    root = Path(root)
    return [SourceFile(p, str(p.relative_to(root)), origin(p.relative_to(root)))
            for p in walk(root) if p.suffix in SOURCE_SUFFIXES]


def build_files(root: Path) -> list[Path]:
    return [p for p in walk(Path(root)) if p.name in BUILD_NAMES or p.name == CATALOG]
