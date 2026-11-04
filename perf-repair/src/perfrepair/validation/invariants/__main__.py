"""python3 -m perfrepair.validation.invariants <device folder> — every grouping and scoping invariant; exit 1 on a blocking one."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..finding import BLOCKING, blocking, counts
from . import run_invariants


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m perfrepair.validation.invariants", description=__doc__.strip())
    parser.add_argument("device", type=Path, help="a device folder: grouping/ and one folder per app")
    parser.add_argument("--apps", type=Path, help="the folder holding the app trees, when app.json's root moved")
    parser.add_argument("--against", type=Path, help="another device folder: grouping stability between the two")
    parser.add_argument("--json", type=Path, help="write the findings and counts here too")
    args = parser.parse_args(argv)
    if not args.device.is_dir():
        parser.error(f"not a directory: {args.device}")
    found = run_invariants(args.device, args.apps, args.against)
    for v in sorted(found, key=lambda v: (v.severity != BLOCKING, v.invariant, v.subject)):
        print(v.line())
    table = counts(found)
    for name, by in table.items():
        print(f"{name}: " + ", ".join(f"{n} {s}" for s, n in sorted(by.items())))
    print(f"invariants: {len(blocking(found))} blocking, {len(found) - len(blocking(found))} other")
    if args.json:
        args.json.write_text(json.dumps({"counts": table, "findings": [v.to_json() for v in found]}, indent=1) + "\n")
    return 1 if blocking(found) else 0


if __name__ == "__main__":
    sys.exit(main())
