"""An app's project name beside its id, for people: a Gradle rootProject.name, else its folder; the id stays the key."""
from __future__ import annotations

import re
from pathlib import Path

ROOT_NAME = re.compile(r"""rootProject\.name\s*=\s*["']([^"']+)["']""")
SETTINGS = ("settings.gradle.kts", "settings.gradle")


def project_name(root: str | Path) -> str:
    """A source tree moved or gone since the app step names its folder."""
    for name in SETTINGS:
        path = Path(root) / name
        found = ROOT_NAME.search(path.read_text(errors="replace")) if path.is_file() else None
        if found:
            return found.group(1)
    return Path(root).name
