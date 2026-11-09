#!/usr/bin/env python3
"""Path rules for the Python outside lib/cryptobench/cryptobench/paths/, minus paths-frozen.txt; every data file has a production reader."""
from __future__ import annotations

import argparse
import ast
import pathlib
import sys

from cryptobench import paths

ROOT = paths.code_root()
FROZEN = ROOT / "tools/paths-frozen.txt"
SOURCES = ("apps/benchmark-runner", "apps/cli", "apps/perf-repair/src", "lib/cryptobench", "tools")
INTERFACE = "lib/cryptobench/cryptobench/paths"
SKIPPED = {"tests", "fixtures", "build", "__pycache__"}
REPO_PREFIXES = ("apps/", "lib/", "config/", "algorithms/", "tools/")
ENV_READS = ("CRYPTOBENCH_ROOT", "ANDROID_HOME")
PRODUCTION_SUFFIXES = (".py", ".kt", ".kts", ".gradle")


def _docstrings(tree: ast.AST) -> set[int]:
    return {id(node.body[0].value) for node in ast.walk(tree)
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)}


def _in_fstring(tree: ast.AST) -> set[int]:
    return {id(part) for node in ast.walk(tree) if isinstance(node, ast.JoinedStr) for part in ast.walk(node)}


def _sources() -> list[pathlib.Path]:
    found = []
    for source in SOURCES:
        for path in sorted((ROOT / source).rglob("*.py")):
            relative = path.relative_to(ROOT)
            if SKIPPED.isdisjoint(relative.parts) and not relative.is_relative_to(INTERFACE) and relative.name != "paths_check.py":
                found.append(path)
    return found


def _rules(tree: ast.AST) -> set[str]:
    docs, fragments, found = _docstrings(tree), _in_fstring(tree), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "__file__":
            found.add("__file__")
        elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) and node.value.attr == "parents":
            found.add(".parents[")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            call = node.func
            if call.attr == "with_name":
                found.add("with_name(")
            elif call.attr in ("insert", "append", "extend") and isinstance(call.value, ast.Attribute) and call.value.attr == "path":
                if getattr(call.value.value, "id", "") == "sys":
                    found.add("sys.path")
            elif call.attr == "home" and getattr(call.value, "attr", getattr(call.value, "id", "")) == "Path":
                found.add("Path.home()")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs:
            text = node.value
            if text == "PYTHONPATH":
                found.add("PYTHONPATH")
            elif text in ENV_READS:
                found.add(f"env {text}")
            elif text in paths.CONTRACT and id(node) not in fragments:
                found.add(f"contract {text}")
            elif text.startswith(REPO_PREFIXES) and "/" in text and " " not in text and id(node) not in fragments:
                found.add(f"repo path {text}")
    return found


def path_violations() -> set[str]:
    found = set()
    for path in _sources():
        relative = path.relative_to(ROOT).as_posix()
        found |= {f"{relative}: {rule}" for rule in _rules(ast.parse(path.read_text(encoding="utf-8")))}
    return found


def _strings_of_production() -> set[str]:
    strings = set()
    for source in ("apps", "lib", "tools"):
        for path in (ROOT / source).rglob("*"):
            if path.suffix not in PRODUCTION_SUFFIXES or not SKIPPED.isdisjoint(path.relative_to(ROOT).parts) or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if path.suffix == ".py":
                strings |= {n.value for n in ast.walk(ast.parse(text)) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
            else:
                strings.add(text)
    return strings


def _read_in(strings: set[str], data: pathlib.Path) -> bool:
    name = data.name
    candidates = {name, data.stem, name.split("_")[-1], "vectors" if data.parent.name == "vectors" else name}
    # a Gradle or Kotlin file names the file in its text; Python holds the name as a whole string, or a suffix a reader globs
    return any(c in strings for c in candidates) or any(name in s or (s.startswith("_") and name.endswith(s)) for s in strings if len(s) < 4000)


def unread_data() -> set[str]:
    strings = _strings_of_production()
    found = {f"unread data: algorithms/{p.relative_to(paths.repo().algorithms).as_posix()}"
             for p in paths.repo().algorithms.rglob("*") if p.is_file() and not _read_in(strings, p)}
    used = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in (ROOT / "apps/perf-repair/src").rglob("*.py"))
    for name in dir(paths):
        entry = getattr(paths, name)
        if isinstance(entry, paths.PackagedFile) and entry in paths.ALL_PACKAGED and f"paths.{name}" not in used:
            found.add(f"unread data: {entry.package}/{entry.name}")
    return found


def check(found: set[str], frozen: pathlib.Path, shrink: bool) -> list[str]:
    kept = {line for line in frozen.read_text().splitlines() if line.strip() and not line.startswith("#")} if frozen.is_file() else set()
    kept_entries = {line.split(" # ")[0].rstrip() for line in kept}
    stale = kept_entries - found
    if shrink and stale:
        frozen.write_text("".join(f"{line}\n" for line in sorted(kept) if line.split(" # ")[0].rstrip() in found))
        stale = set()
    return [f"new: {line}" for line in sorted(found - kept_entries)] + [f"fixed, remove from {frozen.name} (--shrink): {line}" for line in sorted(stale)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shrink", action="store_true", help=f"drop fixed entries from {FROZEN.name}; never adds one")
    args = parser.parse_args()
    found = path_violations() | unread_data()
    problems = check(found, FROZEN, args.shrink)
    for line in problems:
        print(line)
    print("paths: ok" if not problems else f"paths: {len(problems)} problem(s)", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
