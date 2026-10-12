"""python3 -m perfrepair.orchestrate worthiness --run <dir> --mode latency|battery — the worthiness decision stage.

Grouping runs first: python3 -m perfrepair.grouping {build,assign,report}.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..result.modes import MODES
from .agent import ClaudeAgent
from .commands import worthiness as worthiness_cmd


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="perfrepair.orchestrate", description=__doc__)
    sub = ap.add_subparsers(dest="stage", required=True)
    p = sub.add_parser("worthiness")
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--mode", required=True, choices=sorted(MODES))
    p.add_argument("--agent", choices=["claude", "dry-run"], default="claude")
    p.add_argument("--model", default="claude-opus-5-5")
    p.add_argument("--effort", default="medium", choices=["low", "medium", "high", "xhigh", "max"])
    p.add_argument("--attempts", type=int, default=2)
    a = ap.parse_args(argv)
    agent = worthiness_cmd.DRY_RUN if a.agent == "dry-run" else ClaudeAgent(a.model, a.effort)
    worthiness_cmd.worthiness(a.run, MODES[a.mode], agent, a.attempts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
