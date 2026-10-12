"""python3 -m perfrepair.orchestrate worthiness --run <dir> --mode latency|battery [--agent ...] — after grouping."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..result.modes import MODES
from .agent.select import add_agent_args, conversations
from .commands import worthiness as worthiness_cmd
from .engine.ask import Limits


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="perfrepair.orchestrate", description=__doc__)
    sub = ap.add_subparsers(dest="stage", required=True)
    p = sub.add_parser("worthiness")
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--mode", required=True, choices=sorted(MODES))
    add_agent_args(p)
    p.add_argument("--turns", type=int, default=Limits.turns)
    p.add_argument("--sessions", type=int, default=Limits.sessions)
    p.add_argument("--limit", type=int)
    a = ap.parse_args(argv)
    worthiness_cmd.worthiness(a.run, MODES[a.mode], conversations(a, worthiness_cmd.DRY_RUN),
                              Limits(a.turns, a.sessions), a.limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
