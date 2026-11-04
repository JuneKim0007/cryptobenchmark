#!/usr/bin/env python3
"""Forwards to `python3 -m perfrepair guide` with perf-repair/src on the path; arguments pass through unchanged."""
import sys

import dependencies  # noqa: F401  first: it reports a missing PyYAML, which perfrepair needs
from repo import ROOT

sys.path.insert(0, str(ROOT / "perf-repair" / "src"))

from perfrepair.guide.command import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
