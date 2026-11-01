"""python3 -m perfrepair.report app --run <dir> --app <name> [--mode latency|battery] — apps/<app>/report.json, .md;
   python3 -m perfrepair.report summary --run <dir> — apps/summary.json, .md over every app's report.json."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..result.modes import MODES
from ..validation import ValidationFailed
from .command import app_report, run_summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="perfrepair.report", description=__doc__)
    sub = ap.add_subparsers(dest="step", required=True)
    p = sub.add_parser("app")
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--app", required=True)
    p.add_argument("--mode", choices=sorted(MODES), default="latency")
    sub.add_parser("summary").add_argument("--run", type=Path, required=True)
    a = ap.parse_args(argv)
    try:
        if a.step == "app":
            app_report(a.run, a.app, MODES[a.mode])
        else:
            run_summary(a.run)
    except (FileNotFoundError, ValueError, ValidationFailed) as e:
        print(f"error {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
