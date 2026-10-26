"""python3 -m perfrepair.ai worthiness --run <dir> --mode latency|battery [--agent ...] [--prompts DIR] — after grouping."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..result.modes import MODES
from .runtime.agent.select import add_agent_args, conversations
from .evaluate.worthiness import command as worthiness_cmd
from .runtime.engine.ask import Limits
from .runtime.prompt.args import add_prompt_args, load_prompts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="perfrepair.ai", description=__doc__)
    sub = ap.add_subparsers(dest="stage", required=True)
    p = sub.add_parser("worthiness")
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--mode", required=True, choices=sorted(MODES))
    add_agent_args(p)
    add_prompt_args(p)
    p.add_argument("--turns", type=int, default=Limits.turns)
    p.add_argument("--sessions", type=int, default=Limits.sessions)
    p.add_argument("--limit", type=int)
    a = ap.parse_args(argv)
    library = load_prompts(ap, a)
    worthiness_cmd.worthiness(a.run, MODES[a.mode], conversations(a, worthiness_cmd.DRY_RUN), library,
                              Limits(a.turns, a.sessions), a.limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
