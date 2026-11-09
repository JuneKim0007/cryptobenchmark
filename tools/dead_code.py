#!/usr/bin/env python3
"""Dead-code check: vulture over the Python apps and tools, minus tools/dead-code-allow.txt; a local tool, never run in CI."""
from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

from cryptobench import paths

ROOT = paths.code_root()
ALLOW = ROOT / "tools/dead-code-allow.txt"
VULTURE = pathlib.Path(os.environ.get("VULTURE", paths.home() / "capstone/tools/venv/bin/vulture"))
TARGETS = ("apps/perf-repair/src", "apps/benchmark-runner", "apps/cli", "lib/cryptobench", "tools")
EXCLUDE = "*/tests/*,*/tests,*/fixtures/*"
FINDING = re.compile(r"^(\S+?):\d+: unused \w+ '(\w+)'")


def allowed() -> dict[str, str]:
    lines = [line for line in ALLOW.read_text().splitlines() if line.strip() and not line.startswith("#")]
    entries = dict(line.split(" : ", 1) for line in lines if " : " in line)
    if len(entries) != len(lines) or not all(entries.values()):
        sys.exit(f"dead-code: {ALLOW.name}: every line is <path>:<name> : <reason>")
    return entries


def main() -> int:
    if not VULTURE.is_file():
        sys.exit(f"dead-code: no vulture at {VULTURE}; install it there or set VULTURE")
    out = subprocess.run([str(VULTURE), *TARGETS, "--exclude", EXCLUDE], cwd=ROOT, capture_output=True, text=True).stdout
    found = {f"{m.group(1)}:{m.group(2)}": line for line in out.splitlines() if (m := FINDING.match(line))}
    entries = allowed()
    problems = [line for key, line in sorted(found.items()) if key not in entries]
    problems += [f"{ALLOW.name}: {key} matches no finding; remove it" for key in sorted(set(entries) - set(found))]
    for line in problems:
        print(line)
    print("dead-code: ok" if not problems else f"dead-code: {len(problems)} problem(s)", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
