"""python3 -m perfrepair.report app --device-results <dir> --app <source> [--mode latency|battery] — <dir>/<app>/report.json, .md;
   python3 -m perfrepair.report summary --device-results <dir> — <dir>/summary.json, .md over every app's report.json."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..app.facts.path_id import app_id
from ..config.args import add_config_arg
from ..config.device_results import add_device_results_arg, fill_device_results
from ..log import log_to_stderr
from ..result.modes import MODES
from ..failure import reported
from .command import app_report, device_summary


def main(argv: list[str] | None = None) -> int:
    log_to_stderr()
    ap = argparse.ArgumentParser(prog="perfrepair.report", description=__doc__)
    sub = ap.add_subparsers(dest="step", required=True)
    p = sub.add_parser("app")
    p.add_argument("--app", type=Path, required=True, help="the app's source folder; its path gives the app's id")
    p.add_argument("--mode", choices=sorted(MODES), default="latency")
    for step in (p, sub.add_parser("summary")):
        add_device_results_arg(step)
        add_config_arg(step)
    a = ap.parse_args(argv)
    return reported(lambda: _step(ap, a))


def _step(ap: argparse.ArgumentParser, a: argparse.Namespace) -> None:
    fill_device_results(ap, a)
    if a.step == "app":
        app_report(a.device_results, app_id(a.device_results, a.app), MODES[a.mode])
    else:
        device_summary(a.device_results)


if __name__ == "__main__":
    sys.exit(main())
