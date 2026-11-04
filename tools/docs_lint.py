#!/usr/bin/env python3
from __future__ import annotations

import os
import posixpath
import re
import sys

from lint.markdown import map_blocks
from lint.paths import ENTRY, ROUTERS, is_doc, join, router_of
from lint.tree import ROOT, Tree, tracked

LINE_LIMIT = 150
UNMAPPED_OK = {".gitignore", "gradlew", "gradlew.bat"}
GENERATED = {"build", ".gradle", ".venv", "node_modules", ".kotlin", "__pycache__"}
BANNED = [(re.compile(r"20\d\d-\d\d-\d\d"), "date"), (re.compile(r"TODO"), "TODO"), (re.compile("—"), "em dash")]
GUIDE_EDGE = re.compile(r"(^|[^A-Za-z0-9_-])agents/|AGENTS\.md")


def entries() -> list[str]:
    return [f"{join(r, ENTRY)}: missing" for r in ROUTERS if not (ROOT / join(r, ENTRY)).is_file()]


def maps(tree: Tree, problems: list[str]) -> dict[str, str]:
    owners: dict[str, str] = {}
    for p in tree.md:
        r = router_of(p)
        for block in map_blocks(p, tree.text[p]):
            for prev, cur in zip(block, block[1:]):
                if prev > cur:
                    problems.append(f"{p}: map not sorted: {cur} after {prev}")
            for entry in block:
                full = join(r, entry.rstrip("/")) + ("/" if entry.endswith("/") else "")
                if not tree.exists(full.rstrip("/")):
                    problems.append(f"{p}: mapped path {entry} does not exist")
                if full in owners and owners[full] != p:
                    problems.append(f"{full}: mapped in {owners[full]} and {p}")
                owners.setdefault(full, p)
    return owners


def coverage(tree: Tree, owners: dict[str, str]) -> list[str]:
    def covered(path: str) -> bool:
        if path in owners:
            return True
        d = posixpath.dirname(path)
        while d:
            if d + "/" in owners:
                return True
            d = posixpath.dirname(d)
        return False
    return [f"{p}: not covered by any map line or folder line" for p in tree.files
            if not (posixpath.basename(p) in UNMAPPED_OK or "gradle/wrapper/" in p) and not covered(p)]


def doc_indexes(tree: Tree) -> list[str]:
    doc_dirs = set()
    for p in tree.md:
        if is_doc(p):
            d = posixpath.dirname(p)
            while d and posixpath.basename(d) != "docs":
                doc_dirs.add(d)
                d = posixpath.dirname(d)
            doc_dirs.add(d)
    return [f"{d}/: docs folder has no index.md" for d in sorted(doc_dirs) if join(d, "index.md") not in tree.fileset]


def contents(tree: Tree) -> list[str]:
    problems = []
    for p in tree.md:
        for token, link in tree.references(p):
            path = tree.resolve(p, token, link)
            if path is None or any(seg in GENERATED for seg in path.split("/")):
                continue
            if not tree.exists(path):
                problems.append(f"{p}: {'link' if link else 'path'} {token} does not exist")
        if is_doc(p):
            for n, line in enumerate(tree.text[p].splitlines(), 1):
                if GUIDE_EDGE.search(line):
                    problems.append(f"{p}:{n}: doc links to a guide")
        lines = tree.text[p].splitlines()
        if len(lines) > LINE_LIMIT:
            problems.append(f"{p}: {len(lines)} lines, limit {LINE_LIMIT}")
        for n, line in enumerate(lines, 1):
            for pattern, name in BANNED:
                if pattern.search(line):
                    problems.append(f"{p}:{n}: {name}")
    return problems


def unreachable(tree: Tree) -> list[str]:
    reached, todo = set(), [ENTRY]
    while todo:
        p = todo.pop()
        if p in reached or p not in tree.text:
            continue
        reached.add(p)
        for token, link in tree.references(p):
            path = tree.resolve(p, token, link)
            if path is None:
                continue
            if path in tree.dirs and join(path, "index.md") in tree.fileset:
                path = join(path, "index.md")
            if path.endswith(".md"):
                todo.append(path)
    return [f"{p}: not reachable from {ENTRY}" for p in tree.md if p not in reached]


def main() -> int:
    tree = Tree(tracked())
    problems = entries()
    owners = maps(tree, problems)
    problems += coverage(tree, owners) + doc_indexes(tree) + contents(tree) + unreachable(tree)
    for line in problems:
        print(line)
    print("docs-lint: ok" if not problems else f"docs-lint: {len(problems)} problem(s)", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    os.chdir(ROOT)
    sys.exit(main())
