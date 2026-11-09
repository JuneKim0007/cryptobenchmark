#!/usr/bin/env python3
"""Kotlin file names: the :files module equals Python's CONTRACT, and no file name is written by hand outside it."""
from __future__ import annotations

import pathlib
import re
import sys

from cryptobench import paths

ROOT = paths.code_root()
MODULE = paths.repo().kotlin_files_module
SOURCES = paths.repo().kotlin_name_users
OWNER = re.compile(r"^object (\w+)", re.M)
CONSTANT = re.compile(r'^\s*const val (\w+) = "([^"]*)"', re.M)
LITERAL = re.compile(r'"(?:[^"\\]|\\.)*"')
HAND_BUILT = re.compile(r'\bFile\([^"]*,\s*"[\w.]')


def kotlin_names(module: pathlib.Path) -> dict[str, str]:
    found = {}
    for path in sorted(module.rglob("*.kt")):
        text = path.read_text(encoding="utf-8")
        owner = OWNER.search(text)
        if owner:
            found |= {f"{owner.group(1)}.{name}": value for name, value in CONSTANT.findall(text)}
    return found


def disagreements(kotlin: dict[str, str], contract: dict[str, str]) -> list[str]:
    python = {constant: name for name, constant in contract.items()}
    problems = [f"kotlin only: {c} = {kotlin[c]}" for c in sorted(kotlin.keys() - python.keys())]
    problems += [f"python only: {c} = {python[c]}" for c in sorted(python.keys() - kotlin.keys())]
    return problems + [f"differs: {c}: kotlin {kotlin[c]}, python {python[c]}" for c in sorted(kotlin.keys() & python.keys()) if kotlin[c] != python[c]]


def _code_lines(path: pathlib.Path) -> list[str]:
    return [line for line in path.read_text(encoding="utf-8").splitlines() if not line.strip().startswith(("//", "/*", "*"))]


def literal_violations(repo: pathlib.Path, sources: tuple[pathlib.Path, ...], kotlin: dict[str, str]) -> set[str]:
    names = [value for constant, value in kotlin.items() if constant.startswith("FileNames.")]
    named = re.compile(r"(?<![\w.-])(?:" + "|".join(map(re.escape, names)) + r")(?![\w.-])")
    found = set()
    for source in sources:
        for path in sorted(source.rglob("*.kt")):
            relative = path.relative_to(repo).as_posix()
            for line in _code_lines(path):
                found |= {f"{relative}: names {hit}" for literal in LITERAL.findall(line) for hit in named.findall(literal)}
                if HAND_BUILT.search(line):
                    found.add(f"{relative}: builds a file from a literal: {line.strip()[:80]}")
    return found


def main() -> int:
    kotlin = kotlin_names(MODULE)
    problems = disagreements(kotlin, paths.CONTRACT | paths.CONTRACT_PARTS) + sorted(literal_violations(ROOT, SOURCES, kotlin))
    for line in problems:
        print(line)
    print("names: ok" if not problems else f"names: {len(problems)} problem(s)", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
