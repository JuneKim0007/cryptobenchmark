#!/usr/bin/env python3
"""Forwards to `python3 -m perfrepair guide` with perf-repair/src on the path; arguments pass through unchanged."""
import pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "perf-repair" / "src"))

from perfrepair.guide.command import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
