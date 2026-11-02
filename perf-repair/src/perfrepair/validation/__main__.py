"""python3 -m perfrepair.validation <run dir> — validate every artifact; exit 1 on any problem."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..check.run import validate_run
from ..config.args import add_config_arg, load_settings
from ..failure import reported
from ..log import log_to_stderr
from ..screen.catalog import screening_catalog


def main(argv: list[str] | None = None) -> int:
    log_to_stderr()
    parser = argparse.ArgumentParser(prog="python3 -m perfrepair.validation", description=__doc__.strip())
    parser.add_argument("run", type=Path, help="run directory")
    add_config_arg(parser)
    args = parser.parse_args(argv)
    if not args.run.is_dir():
        parser.error(f"not a directory: {args.run}")
    try:
        catalog = screening_catalog(load_settings(parser, args))
    except ValueError as e:
        parser.error(str(e))
    return reported(lambda: _print(validate_run(args.run, catalog)))


def _print(report: dict[str, list[str]]) -> int:
    for artifact, problems in report.items():
        print(f"{artifact}: {'ok' if not problems else f'{len(problems)} problem(s)'}")
        for p in problems:
            print(f"  - {p}")
    return 1 if any(report.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
