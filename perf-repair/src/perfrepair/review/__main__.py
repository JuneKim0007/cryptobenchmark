"""python3 -m perfrepair.review sheet|score <device>: writes <device>/review/decisions.tsv, then prints what its verdicts score."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..failure import reported
from .score import score
from .sheet import write_sheet


def _sheet(device: Path) -> None:
    print(f"{len(write_sheet(device))} decisions")


def _score(device: Path) -> None:
    write_sheet(device)
    print(json.dumps(score(device), indent=1))


COMMANDS = {"sheet": _sheet, "score": _score}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="perfrepair.review", description=__doc__)
    ap.add_argument("command", choices=sorted(COMMANDS))
    ap.add_argument("device", type=Path, help="the device folder")
    a = ap.parse_args(argv)
    return reported(lambda: COMMANDS[a.command](a.device))


if __name__ == "__main__":
    sys.exit(main())
