"""python3 -m perfrepair.validation <run dir> — validate every artifact; exit 1 on any problem."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..check.run import validate_run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m perfrepair.validation", description=__doc__.strip())
    parser.add_argument("run", type=Path, help="run directory")
    run = parser.parse_args(argv).run
    if not run.is_dir():
        parser.error(f"not a directory: {run}")
    report = validate_run(run)
    for artifact, problems in report.items():
        print(f"{artifact}: {'ok' if not problems else f'{len(problems)} problem(s)'}")
        for p in problems:
            print(f"  - {p}")
    return 1 if any(report.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
