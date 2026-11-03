"""The pinned version of each group:name the build files declare: a literal coordinate, a Gradle map, or a version
catalog entry with its version or version.ref; anything else (a variable, a range) has none."""
from __future__ import annotations

import re
from pathlib import Path

from ...dto.version import newest

_LITERAL = re.compile(r"""["']([\w.\-]+):([\w.\-]+):([^"'\s:@]+)(?:@\w+)?["']""")
_VERSION = r"""(?:version\s*[:=]\s*["']([^"']+)["']|version\.ref\s*=\s*["']([^"']+)["'])"""
_MAP = re.compile(r"""group\s*[:=]\s*["']([\w.\-]+)["']\s*,\s*name\s*[:=]\s*["']([\w.\-]+)["']\s*,\s*""" + _VERSION)
_MODULE = re.compile(r"""module\s*=\s*["']([\w.\-]+):([\w.\-]+)["']\s*,\s*""" + _VERSION)
_TABLE = re.compile(r"^\s*\[(\w+)\]\s*$")
_ENTRY = re.compile(r"""^\s*([\w.\-]+)\s*=\s*["']([^"']+)["']""")


def _catalog_versions(text: str) -> dict[str, str]:
    """The [versions] table of a libs.versions.toml."""
    out, table = {}, None
    for line in text.splitlines():
        if m := _TABLE.match(line):
            table = m.group(1)
        elif table == "versions" and (m := _ENTRY.match(line)):
            out[m.group(1)] = m.group(2)
    return out


def _declared(text: str, refs: dict[str, str]) -> list[tuple[str, str | None]]:
    found = [(f"{m.group(1)}:{m.group(2)}", m.group(3)) for m in _LITERAL.finditer(text)]
    for pattern in (_MAP, _MODULE):
        found += [(f"{m.group(1)}:{m.group(2)}", m.group(3) or refs.get(m.group(4))) for m in pattern.finditer(text)]
    return found


def pinned_versions(texts: list[tuple[Path, str]]) -> dict[str, str]:
    """texts: each build file with its uncommented text; several pins of one artifact keep the newest, as Gradle does."""
    refs = {k: v for path, text in texts if path.suffix == ".toml" for k, v in _catalog_versions(text).items()}
    pins: dict[str, list[str]] = {}
    for _, text in texts:
        for artifact, version in _declared(text, refs):
            pins.setdefault(artifact, []).append(version)
    return {a: v for a, found in pins.items() if (v := newest(found))}
