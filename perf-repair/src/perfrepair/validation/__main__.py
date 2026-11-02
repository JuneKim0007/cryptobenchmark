"""python3 -m perfrepair.validation --device-results <dir> — validate every artifact; exit 1 on any problem."""
from __future__ import annotations

import argparse
import sys

from ..check.run import validate_run
from ..config.args import add_config_arg, load_settings
from ..config.device_results import add_device_results_arg, fill_device_results
from ..failure import reported
from ..log import log_to_stderr
from ..screen.catalog import screening_catalog


def main(argv: list[str] | None = None) -> int:
    log_to_stderr()
    parser = argparse.ArgumentParser(prog="python3 -m perfrepair.validation", description=__doc__.strip())
    add_device_results_arg(parser)
    add_config_arg(parser)
    args = parser.parse_args(argv)
    settings = load_settings(parser, args)
    try:
        fill_device_results(parser, args, settings)
        catalog = screening_catalog(settings)
    except ValueError as e:
        parser.error(str(e))
    if not args.device_results.is_dir():
        parser.error(f"not a directory: {args.device_results}")
    return reported(lambda: _print(validate_run(args.device_results, catalog)))


def _print(report: dict[str, list[str]]) -> int:
    for artifact, problems in report.items():
        print(f"{artifact}: {'ok' if not problems else f'{len(problems)} problem(s)'}")
        for p in problems:
            print(f"  - {p}")
    return 1 if any(report.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
