"""python3 -m perfrepair.ai worthiness --device-results <dir> --mode latency|battery — after grouping;
   python3 -m perfrepair.ai replace --device-results <dir> --app <source> — after dossiers. Both take [--agent ...] [--prompts DIR]
   and read perfrepair.yaml (--perfrepair-config FILE); see docs/settings.md."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..app.facts.path_id import app_id
from ..config.args import load_settings, positive_int
from ..config.device_results import add_device_results_arg, fill_device_results
from ..failure import reported
from ..inputs.table import APPS_REPLACE, WORTHINESS, RoleRow
from ..log import attach
from ..result.modes import MODES
from .runtime.gateway.args import add_agent_args
from .runtime.gateway.spawn import spawn
from .evaluate.worthiness import command as worthiness_cmd
from .suggest.site_replace import command as replace_cmd
from .runtime.engine.ask import Limits
from .runtime.prompt.args import add_prompt_args, load_prompts


def _engine_args(p: argparse.ArgumentParser, role: RoleRow) -> None:
    add_agent_args(p, role=role)
    add_prompt_args(p)
    p.add_argument("--turns", type=positive_int, default=Limits.turns)
    p.add_argument("--sessions", type=positive_int, default=Limits.sessions)
    p.add_argument("--limit", type=positive_int)


def main(argv: list[str] | None = None) -> int:
    attach()
    ap = argparse.ArgumentParser(prog="perfrepair.ai", description=__doc__)
    sub = ap.add_subparsers(dest="stage", required=True)
    p = sub.add_parser("worthiness")
    add_device_results_arg(p)
    p.add_argument("--mode", required=True, choices=sorted(MODES))
    _engine_args(p, WORTHINESS)
    p = sub.add_parser("replace")
    add_device_results_arg(p)
    p.add_argument("--app", type=Path, required=True, help="the app's source folder; its path gives the app's id")
    _engine_args(p, APPS_REPLACE)
    a = ap.parse_args(argv)
    return reported(lambda: _stage(ap, a))


def _stage(ap: argparse.ArgumentParser, a: argparse.Namespace) -> None:
    settings = load_settings(ap, a)
    fill_device_results(ap, a, settings)
    attach(a.device_results)
    library = load_prompts(ap, a, settings)
    limits = Limits(a.turns, a.sessions)
    if a.stage == "worthiness":
        worthiness_cmd.worthiness(a.device_results, MODES[a.mode], spawn(a, settings, worthiness_cmd.DRY_RUN), library, limits, a.limit)
    else:
        replace_cmd.replace(a.device_results, app_id(a.device_results, a.app), spawn(a, settings, replace_cmd.DRY_RUN), library, limits, a.limit)


if __name__ == "__main__":
    sys.exit(main())
