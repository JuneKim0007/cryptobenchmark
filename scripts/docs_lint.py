#!/usr/bin/env python3
from __future__ import annotations

import os
import posixpath
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROUTERS = ("", "perf-repair")
ENTRY, ENTRY_COPY = "AGENTS.md", "CLAUDE.md"
LINE_LIMIT = 150
NOT_GRAPHED = {"modules/environment/discovery/docs/tree.md", "tools/quick-bench/tests/golden_summary.md"}
UNMAPPED_OK = {"CLAUDE.md", ".gitignore", "gradlew", "gradlew.bat"}
GENERATED = {"build", ".gradle", ".venv", "node_modules", ".kotlin", "__pycache__"}
BANNED = [(re.compile(r"20\d\d-\d\d-\d\d"), "date"), (re.compile(r"TODO"), "TODO"), (re.compile("—"), "em dash")]
MAP_LINE = re.compile(r"^(\S+) : \S")
BACKTICK = re.compile(r"`([^`\n]+)`")
LINK = re.compile(r"\]\(([^)\s]+)\)")
GUIDE_EDGE = re.compile(r"(^|[^A-Za-z0-9_-])agents/|AGENTS\.md")


def tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                         cwd=ROOT, capture_output=True, check=True).stdout.decode()
    return sorted({p for p in out.split("\0") if p and (ROOT / p).is_file()})


def router_of(path: str) -> str:
    return next((r for r in ROUTERS if r and path.startswith(r + "/")), "")


def local(path: str) -> str:
    r = router_of(path)
    return path[len(r) + 1:] if r else path


def join(base: str, rel: str) -> str:
    return posixpath.normpath(posixpath.join(base, rel)) if base else posixpath.normpath(rel)


def is_guide(path: str) -> bool:
    rel = local(path)
    return rel == ENTRY or rel.startswith("agents/")


def is_doc(path: str) -> bool:
    return not is_guide(path) and "docs" in local(path).split("/")[:-1]


def graphed(path: str) -> bool:
    return path.endswith(".md") and not path.endswith(".system.md") and path not in NOT_GRAPHED \
        and (is_guide(path) or is_doc(path))


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


def main() -> int:
    files = tracked()
    fileset = set(files)
    dirs = {posixpath.dirname(p) for p in files}
    for d in list(dirs):
        while d:
            d = posixpath.dirname(d)
            dirs.add(d)
    md = [p for p in files if graphed(p)]
    text = {p: (ROOT / p).read_text(encoding="utf-8") for p in files if p.endswith(".md")}
    tops = {r: {(local(p) if r else p).split("/")[0] for p in files if router_of(p) == r or not r} for r in ROUTERS}
    problems: list[str] = []

    def exists(path: str) -> bool:
        return path in fileset or path in dirs or (ROOT / path).exists()

    for r in ROUTERS:
        entry, copy = join(r, ENTRY), join(r, ENTRY_COPY)
        if not (ROOT / entry).is_file():
            problems.append(f"{entry}: missing")
        elif not (ROOT / copy).is_file() or (ROOT / copy).read_bytes() != (ROOT / entry).read_bytes():
            problems.append(f"{copy}: not a byte copy of {entry}; run cp {ENTRY} {ENTRY_COPY}")

    owners: dict[str, str] = {}
    for p in md:
        r = router_of(p)
        for block in map_blocks(p, text[p]):
            for prev, cur in zip(block, block[1:]):
                if prev > cur:
                    problems.append(f"{p}: map not sorted: {cur} after {prev}")
            for entry in block:
                full = join(r, entry.rstrip("/")) + ("/" if entry.endswith("/") else "")
                if not exists(full.rstrip("/")):
                    problems.append(f"{p}: mapped path {entry} does not exist")
                if full in owners and owners[full] != p:
                    problems.append(f"{full}: mapped in {owners[full]} and {p}")
                owners.setdefault(full, p)

    def covered(path: str) -> bool:
        if path in owners:
            return True
        d = posixpath.dirname(path)
        while d:
            if d + "/" in owners:
                return True
            d = posixpath.dirname(d)
        return False

    for p in files:
        if posixpath.basename(p) in UNMAPPED_OK or "gradle/wrapper/" in p:
            continue
        if not covered(p):
            problems.append(f"{p}: not covered by any map line or folder line")

    doc_dirs = set()
    for p in md:
        if is_doc(p):
            d = posixpath.dirname(p)
            while d and posixpath.basename(d) != "docs":
                doc_dirs.add(d)
                d = posixpath.dirname(d)
            doc_dirs.add(d)
    for d in sorted(doc_dirs):
        if join(d, "index.md") not in fileset:
            problems.append(f"{d}/: docs folder has no index.md")

    def resolve(src: str, token: str, link: bool) -> str | None:
        token = clean(token)
        if not token or re.search(r"[<>*{}$|\s]", token) or re.match(r"^[a-z]+:", token):
            return None
        if link:
            return join(posixpath.dirname(src), token)
        r = router_of(src)
        first = token.split("/")[0]
        if first in tops[r] or first in (ENTRY, ENTRY_COPY):
            return join(r, token)
        if first == "..":
            return join(posixpath.dirname(src) if not r else r, token)
        return None

    def references(p: str) -> list[tuple[str, bool]]:
        refs = [(clean(t), False) for t in BACKTICK.findall(text[p])]
        refs += [(e, False) for b in map_blocks(p, text[p]) for e in b]
        refs += [(t, True) for t in LINK.findall(text[p])]
        return refs

    for p in md:
        for token, link in references(p):
            path = resolve(p, token, link)
            if path is None or any(seg in GENERATED for seg in path.split("/")):
                continue
            if not exists(path):
                problems.append(f"{p}: {'link' if link else 'path'} {token} does not exist")
        if is_doc(p):
            for n, line in enumerate(text[p].splitlines(), 1):
                if GUIDE_EDGE.search(line):
                    problems.append(f"{p}:{n}: doc links to a guide")
        lines = text[p].splitlines()
        if len(lines) > LINE_LIMIT:
            problems.append(f"{p}: {len(lines)} lines, limit {LINE_LIMIT}")
        for n, line in enumerate(lines, 1):
            for pattern, name in BANNED:
                if pattern.search(line):
                    problems.append(f"{p}:{n}: {name}")

    reached, todo = set(), [ENTRY]
    while todo:
        p = todo.pop()
        if p in reached or p not in text:
            continue
        reached.add(p)
        for token, link in references(p):
            path = resolve(p, token, link)
            if path is None:
                continue
            if path in dirs and join(path, "index.md") in fileset:
                path = join(path, "index.md")
            if path.endswith(".md"):
                todo.append(path)
    problems += [f"{p}: not reachable from {ENTRY}" for p in md if p not in reached]

    for line in problems:
        print(line)
    print("docs-lint: ok" if not problems else f"docs-lint: {len(problems)} problem(s)", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    os.chdir(ROOT)
    sys.exit(main())
