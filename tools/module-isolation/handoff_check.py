#!/usr/bin/env python3
"""Module references of the consumers in layers.yaml (androidTest, cli) against their handoff lists, minus handoff-frozen.txt."""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

import yaml

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LAYERS = HERE / "layers.yaml"
FROZEN = HERE / "handoff-frozen.txt"


def violations(layers: dict, repo: pathlib.Path) -> set[str]:
    reference = re.compile(re.escape(layers["root"]) + r"\.((?:[a-z]\w*\.)+)([A-Z]\w*|\*)")
    found = set()
    for consumer, spec in layers["consumers"].items():
        sources = repo / spec["sources"]
        for path in sorted(p for p in sources.rglob("*") if p.suffix in (".kt", ".java")):
            body = "\n".join(line for line in path.read_text(encoding="utf-8").splitlines() if not line.startswith("package "))
            for packages, name in reference.findall(body):
                module, _, rest = packages.rstrip(".").partition(".")
                if module not in layers["modules"]:
                    continue
                target = f"{rest}.{name}" if rest else name
                allowed = spec["uses"].get(module, [])
                if allowed != "all" and target not in allowed:
                    found.add(f"{consumer}: {path.relative_to(sources).as_posix()} -> {module}.{target}")
    return found


def check(found: set[str], frozen: pathlib.Path, shrink: bool) -> list[str]:
    kept = {line for line in frozen.read_text().splitlines() if line.strip()} if frozen.is_file() else set()
    stale = kept - found
    if shrink and stale:
        frozen.write_text("".join(f"{line}\n" for line in sorted(kept & found)))
        stale = set()
    problems = [f"new: {line}" for line in sorted(found - kept)]
    return problems + [f"fixed, remove from {frozen.name} (--shrink): {line}" for line in sorted(stale)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shrink", action="store_true", help=f"drop fixed entries from {FROZEN.name}; never adds one")
    args = parser.parse_args()
    found = violations(yaml.safe_load(LAYERS.read_text()), ROOT)
    problems = check(found, FROZEN, args.shrink)
    for line in problems:
        print(line)
    print("handoff: ok" if not problems else f"handoff: {len(problems)} problem(s)", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
