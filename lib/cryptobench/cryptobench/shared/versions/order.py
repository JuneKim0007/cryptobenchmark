"""A Gradle dependency version: whether it is pinned, and Gradle's newest-wins order between pinned ones."""
from __future__ import annotations

import re

# a dynamic version (1.+, latest.release, [1,2)), a variable or a dependency-verification checksum is no pin
_PINNED = re.compile(r"^\d[\w.\-]*$")
_CHECKSUM = re.compile(r"^[0-9a-f]{32,}$")


def pinned(version: str | None) -> bool:
    return bool(version) and bool(_PINNED.match(version)) and not _CHECKSUM.match(version)


def version_key(version: str) -> tuple:
    return tuple((0, int(p), "") if p.isdigit() else (1, 0, p) for p in re.split(r"[.\-]", version))


def newest(versions) -> str | None:
    found = sorted({v for v in versions if pinned(v)}, key=version_key)
    return found[-1] if found else None
