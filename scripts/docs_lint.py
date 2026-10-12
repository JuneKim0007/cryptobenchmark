"""Fails on: a CLAUDE.md that differs from AGENTS.md, a mapped path that does not exist, a path in two
maps, an unsorted map, an unmapped source file, a docs folder without index.md, a .md not reachable
from AGENTS.md, a doc that links to a guide."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAP_LINE = re.compile(r"^(\S+) : \S")
LINK = re.compile(r"`([\w./-]+\.md)`")
SOURCE_GLOBS = ("src/**/*.py", "src/**/*.md", "scripts/*.py")


def guides() -> list[Path]:
    return [ROOT / "AGENTS.md", *sorted((ROOT / "agents").rglob("*.md"))]


def docs() -> list[Path]:
    return sorted((ROOT / "docs").rglob("*.md"))


def maps(md: Path) -> list[list[str]]:
    blocks, inside, current = [], False, []
    for line in md.read_text().splitlines():
        if line.startswith("```"):
            if inside and current:
                blocks.append(current)
            inside, current = not inside, []
        elif inside and (m := MAP_LINE.match(line)):
            current.append(m.group(1))
    return blocks


def main() -> int:
    problems = []
    if (ROOT / "CLAUDE.md").read_bytes() != (ROOT / "AGENTS.md").read_bytes():
        problems.append("CLAUDE.md differs from AGENTS.md")

    owner: dict[str, Path] = {}
    for md in guides() + docs():
        for block in maps(md):
            if block != sorted(block):
                problems.append(f"{md.relative_to(ROOT)}: map is not sorted")
            for path in block:
                if not (ROOT / path).exists():
                    problems.append(f"{md.relative_to(ROOT)}: {path} does not exist")
                if path in owner and owner[path] != md:
                    problems.append(f"{path}: mapped in {owner[path].relative_to(ROOT)} and {md.relative_to(ROOT)}")
                owner.setdefault(path, md)

    sources = {str(p.relative_to(ROOT)) for g in SOURCE_GLOBS for p in ROOT.glob(g)
               if p.name != "__init__.py" and "__pycache__" not in p.parts}
    problems += [f"{s}: not in any map" for s in sorted(sources - set(owner))]

    for folder in {p.parent for p in docs()} | {ROOT / "docs"}:
        if not (folder / "index.md").exists():
            problems.append(f"{folder.relative_to(ROOT)}: no index.md")

    for md in docs():
        problems += [f"{md.relative_to(ROOT)}: links to guide {t}" for t in LINK.findall(md.read_text())
                     if t.startswith("agents/") or t == "AGENTS.md"]

    reached, todo = set(), [ROOT / "AGENTS.md"]
    while todo:
        md = todo.pop()
        if md in reached or not md.exists():
            continue
        reached.add(md)
        todo += [ROOT / t for t in LINK.findall(md.read_text())] + [ROOT / p for b in maps(md) for p in b
                                                                     if p.endswith(".md")]
    problems += [f"{md.relative_to(ROOT)}: not reachable from AGENTS.md" for md in guides() + docs()
                 if md not in reached]

    for p in problems:
        print(p)
    print("docs-lint: ok" if not problems else f"docs-lint: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
