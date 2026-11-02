"""python3 -m perfrepair.ai worthiness --run <dir> --mode latency|battery — after grouping;
   python3 -m perfrepair.ai replace --run <dir> --app <name> — after dossiers. Both take [--agent ...] [--prompts DIR]
   and read perfrepair.yaml (--perfrepair-config FILE); see docs/settings.md."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..config.args import fill, load_settings, positive_int, require
from ..failure import reported
from ..log import log_to_stderr
from ..result.modes import MODES
from .runtime.gateway.args import add_agent_args
from .runtime.gateway.spawn import spawn
from .evaluate.worthiness import command as worthiness_cmd
from .suggest.site_replace import command as replace_cmd
from .runtime.engine.ask import Limits
from .runtime.prompt.args import add_prompt_args, load_prompts


def _engine_args(p: argparse.ArgumentParser, role: str) -> None:
    add_agent_args(p, role=role)
    add_prompt_args(p)
    p.add_argument("--turns", type=positive_int, default=Limits.turns)
    p.add_argument("--sessions", type=positive_int, default=Limits.sessions)
    p.add_argument("--limit", type=positive_int)


def main(argv: list[str] | None = None) -> int:
    log_to_stderr()
    ap = argparse.ArgumentParser(prog="perfrepair.ai", description=__doc__)
    sub = ap.add_subparsers(dest="stage", required=True)
    p = sub.add_parser("worthiness")
    p.add_argument("--run", type=Path, help="default: paths.run in perfrepair.yaml")
    p.add_argument("--mode", required=True, choices=sorted(MODES))
    _engine_args(p, "ai.worthiness")
    p = sub.add_parser("replace")
    p.add_argument("--run", type=Path, help="default: paths.run in perfrepair.yaml")
    p.add_argument("--app", required=True)
    _engine_args(p, "ai.replace")
    a = ap.parse_args(argv)
    return reported(lambda: _stage(ap, a))


def _stage(ap: argparse.ArgumentParser, a: argparse.Namespace) -> None:
    settings = load_settings(ap, a)
    fill(settings, a, {"run": ("paths.run", None), "prompts": ("paths.prompts", None)})
    require(ap, a, "run", "paths.run")
    library = load_prompts(ap, a)
    limits = Limits(a.turns, a.sessions)
    if a.stage == "worthiness":
        worthiness_cmd.worthiness(a.run, MODES[a.mode], spawn(a, settings, worthiness_cmd.DRY_RUN), library, limits, a.limit)
    else:
        replace_cmd.replace(a.run, a.app, spawn(a, settings, replace_cmd.DRY_RUN), library, limits, a.limit)


if __name__ == "__main__":
    sys.exit(main())
