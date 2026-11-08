"""python3 -m perfrepair.ai replace --device-results <dir> --app <source> — after dossiers: Select over the app's broken
   uses, then its units [--agent ...] [--prompts DIR]; reads perfrepair.yaml (--perfrepair-config FILE); see docs/settings.md."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..app.facts.path_id import app_id
from ..config.args import load_settings, positive_int
from ..config.device_results import add_device_results_arg, fill_device_results
from ..failure import reported
from ..inputs.table import APPS_REVIEW
from ..log import attach
from .runtime.engine.ask import Limits
from .runtime.gateway.args import add_agent_args
from .runtime.gateway.spawn import spawn
from .runtime.prompt.args import add_prompt_args, load_prompts
from .select import command as select_cmd


def main(argv: list[str] | None = None) -> int:
    attach()
    ap = argparse.ArgumentParser(prog="perfrepair.ai", description=__doc__)
    sub = ap.add_subparsers(dest="stage", required=True)
    p = sub.add_parser("replace")
    add_device_results_arg(p)
    p.add_argument("--app", type=Path, required=True, help="the app's source folder; its path gives the app's id")
    add_agent_args(p, role=select_cmd.ROLE)
    add_prompt_args(p)
    p.add_argument("--turns", type=positive_int, default=Limits.turns)
    p.add_argument("--sessions", type=positive_int, default=Limits.sessions)
    p.add_argument("--limit", type=positive_int)
    a = ap.parse_args(argv)
    return reported(lambda: _stage(ap, a))


def _stage(ap: argparse.ArgumentParser, a: argparse.Namespace) -> None:
    settings = load_settings(ap, a)
    fill_device_results(ap, a, settings)
    attach(a.device_results)
    library, limits = load_prompts(ap, a, settings), Limits(a.turns, a.sessions)
    app, spawned, review = app_id(a.device_results, a.app), spawn(a, settings, select_cmd.dry_run()), settings.read(APPS_REVIEW)
    upgraded = select_cmd.select_upgrades(a.device_results, app, spawned, library, limits, a.limit, review=review)
    print(f"{app}: {select_cmd.upgrade_counts(upgraded)}")
    select_cmd.select_units(a.device_results, app, spawned, library, limits, a.limit, review=review)


if __name__ == "__main__":
    sys.exit(main())
