"""python3 -m perfrepair.ai worthiness --device-results <dir> --perf-mode generic|<keys> — after grouping;
   python3 -m perfrepair.ai replace --device-results <dir> --app <source> [--refresh] — after dossiers;
   python3 -m perfrepair.ai upgrade --device-results <dir> --app <source> — the broken uses, after dossiers. All take [--agent ...] [--prompts DIR]
   and read perfrepair.yaml (--perfrepair-config FILE); see docs/settings.md."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..app.facts.path_id import app_id
from ..config.args import load_settings, perf_mode, positive_int
from ..config.device_results import add_device_results_arg, fill_device_results
from ..failure import reported
from ..inputs.table import WORTHINESS, RoleRow
from ..log import attach
from ..dto.perf_mode import PerfMode
from ..result.modes import mode_of
from .runtime.gateway.args import add_agent_args
from .runtime.gateway.spawn import spawn
from .evaluate.worthiness import command as worthiness_cmd
from .repair.upgrade import command as upgrade_cmd
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
    p.add_argument("--perf-mode", required=True, type=perf_mode, metavar="KEYS",
                   help="generic, or a comma list of latency, throughput, memAlloc, energy")
    _engine_args(p, WORTHINESS)
    p = sub.add_parser("replace")
    add_device_results_arg(p)
    p.add_argument("--app", type=Path, required=True, help="the app's source folder; its path gives the app's id")
    _engine_args(p, replace_cmd.ROLE)
    p.add_argument("--refresh", action="store_true",
                   help="ask again the scopes whose dossier changed since their decision, into a new outbox; the old one stays; "
                        "default: they stay, flagged stale, and the command exits with dossier_changed")
    p = sub.add_parser("upgrade")
    add_device_results_arg(p)
    p.add_argument("--app", type=Path, required=True, help="the app's source folder; its path gives the app's id")
    _engine_args(p, upgrade_cmd.ROLE)
    a = ap.parse_args(argv)
    return reported(lambda: _stage(ap, a))


def _stage(ap: argparse.ArgumentParser, a: argparse.Namespace) -> None:
    settings = load_settings(ap, a)
    fill_device_results(ap, a, settings)
    attach(a.device_results)
    library = load_prompts(ap, a, settings)
    limits = Limits(a.turns, a.sessions)
    if a.stage == "worthiness":
        worthiness_cmd.worthiness(a.device_results, mode_of(PerfMode.parse(a.perf_mode)), spawn(a, settings, worthiness_cmd.DRY_RUN), library, limits, a.limit)
    elif a.stage == "upgrade":
        upgrade_cmd.upgrade(a.device_results, app_id(a.device_results, a.app), spawn(a, settings, upgrade_cmd.DRY_RUN), library, limits, a.limit)
    else:
        state = replace_cmd.replace(a.device_results, app_id(a.device_results, a.app), spawn(a, settings, replace_cmd.DRY_RUN),
                                    library, limits, a.limit, refresh=a.refresh)
        if replace_cmd.stale_problem(state):
            raise replace_cmd.DossierChanged(replace_cmd.stale_problem(state))


if __name__ == "__main__":
    sys.exit(main())
