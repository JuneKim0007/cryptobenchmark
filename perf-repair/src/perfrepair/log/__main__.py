"""python3 -m perfrepair.log summary <device-results> [--run ID] [--json] — one run of <device>/log/events.jsonl
(the last by default) per stage and per app folder: time, items, model calls, rejections and their top problems,
the slowest items, tokens and cost."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .. import run_dir as rd
from .read import read_events
from .summary import summarize
from .summary_text import summary_lines


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="perfrepair.log", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    s = sub.add_parser("summary")
    s.add_argument("device_results", type=Path, help="the device's results folder, <results root>/<device id>")
    s.add_argument("--run", help="a run id from events.jsonl; default: the last run")
    s.add_argument("--json", action="store_true", help="the summary as JSON")
    a = ap.parse_args(argv)
    path = a.device_results.expanduser() / rd.EVENTS
    try:
        if not path.is_file():
            raise ValueError(f"missing_file: {path}; no command has run on this device folder")
        doc = summarize(read_events(path), a.run)
    except ValueError as e:
        print(f"error {e}", file=sys.stderr)
        return 1
    print(json.dumps(doc, indent=1) if a.json else "\n".join(summary_lines(doc)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
