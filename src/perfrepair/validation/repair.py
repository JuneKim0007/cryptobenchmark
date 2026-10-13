from __future__ import annotations

import re
from pathlib import Path

_LITERAL = re.compile(r'"(?:[^"\\]|\\.)*"')


def validate_patch(patch: dict, root: Path) -> list[str]:
    """The patched line holds the call, and outside string literals the call is unchanged (bar one added provider)."""
    where = f"{patch['file']}:{patch['line']}"
    lines = (root / patch["file"]).read_text().splitlines()
    if not 1 <= patch["line"] <= len(lines) or patch["before"] not in lines[patch["line"] - 1]:
        return [f"{where}: the call is not on that line"]
    shape = lambda text: _LITERAL.sub('""', text)
    before, after = shape(patch["before"]), shape(patch["after"])
    if after not in (before, before.replace('("")', '("", "")', 1)):
        return [f"{where}: the patch changes more than string literals"]
    return [] if patch["before"] != patch["after"] else [f"{where}: the patch changes nothing"]
