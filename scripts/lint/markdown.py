"""What a guide or doc says in markdown: its sections, fenced blocks, map lines and path tokens."""
from __future__ import annotations

import re

from lint.paths import is_doc, is_guide

MAP_LINE = re.compile(r"^(\S+) : \S")
BACKTICK = re.compile(r"`([^`\n]+)`")
LINK = re.compile(r"\]\(([^)\s]+)\)")


def section(text: str, heading: str) -> str:
    keep, fenced, out = False, False, []
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        if not fenced and line.startswith("## "):
            keep = line[3:].strip() == heading
            continue
        if keep:
            out.append(line)
    return "\n".join(out)


def fenced_blocks(text: str) -> list[list[str]]:
    blocks, fence, current = [], None, []
    for line in text.splitlines():
        if line.startswith("```"):
            if fence is None:
                fence, current = line[3:].strip(), []
            else:
                if fence != "mermaid":
                    blocks.append(current)
                fence = None
        elif fence is not None:
            current.append(line)
    return blocks


def map_blocks(path: str, text: str) -> list[list[str]]:
    if is_guide(path):
        source = section(text, "File structure")
    elif is_doc(path) and path.endswith("/index.md"):
        source = text
    else:
        return []
    return [[m.group(1) for line in block if (m := MAP_LINE.match(line))] for block in fenced_blocks(source)]


def clean(token: str) -> str:
    return re.sub(r"#.*$", "", re.sub(r":\d.*$", "", token.strip()))
