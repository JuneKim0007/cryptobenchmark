"""python3 -m perfrepair.watch <device-results> [--from-start] — follows <device>/log/events.jsonl: one line per
finished step, a running counter per model step; exits when a run ends, or on Ctrl-C."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cryptobench.paths import RunTree
from ..log.watch import watch


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="perfrepair.watch", description=__doc__)
    ap.add_argument("device_results", type=Path, help="the device's results folder, <results root>/<device id>")
    ap.add_argument("--from-start", action="store_true", help="print the events already written first")
    ap.add_argument("--interval", type=float, default=0.5, help="seconds between polls; default 0.5")
    a = ap.parse_args(argv)
    try:
        return watch(RunTree(a.device_results.expanduser()).log.events, a.from_start, sys.stdout, sys.stdout.isatty(), a.interval)
    except KeyboardInterrupt:
        print(file=sys.stdout)
        return 130
    except ValueError as e:
        print(f"error {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
