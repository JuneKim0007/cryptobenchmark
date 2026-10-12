"""python3 -m perfrepair.orchestrate worthiness --run <dir> --mode latency|battery — the worthiness decision stage.

Grouping runs first: python3 -m perfrepair.grouping {build,assign,report}.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..result.modes import MODES
from .agent.select import BACKENDS, agent
from .commands import worthiness as worthiness_cmd


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="perfrepair.orchestrate", description=__doc__)
    sub = ap.add_subparsers(dest="stage", required=True)
    p = sub.add_parser("worthiness")
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--mode", required=True, choices=sorted(MODES))
    p.add_argument("--agent", choices=BACKENDS, default="claude")
    p.add_argument("--model", default="claude-opus-5-5")
    p.add_argument("--effort", default="medium", choices=["low", "medium", "high", "xhigh", "max"])
    p.add_argument("--attempts", type=int, default=2)
    a = ap.parse_args(argv)
    worthiness_cmd.worthiness(a.run, MODES[a.mode], agent(a.agent, a.model, a.effort, worthiness_cmd.DRY_RUN), a.attempts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
