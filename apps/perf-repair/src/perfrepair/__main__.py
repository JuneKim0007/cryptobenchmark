"""python3 -m perfrepair guide ... — the one top-level command; every stage keeps its own `-m perfrepair.<stage>`."""
from __future__ import annotations

import sys

from .guide.command import main as guide

COMMANDS = {"guide": guide}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] not in COMMANDS:
        print(f"usage: python3 -m perfrepair {{{','.join(COMMANDS)}}} ...", file=sys.stderr)
        return 2
    return COMMANDS[argv[0]](argv[1:])


if __name__ == "__main__":
    sys.exit(main())
