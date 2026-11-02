"""python3 -m perfrepair.data_handler.inbound — a device's manifest → rows, measurements, run log beside it."""
from __future__ import annotations

import argparse
import sys

from ...config.args import add_config_arg
from ...config.device_results import add_device_results_arg, fill_device_results
from ...device.inbound import write_inbound
from ...failure import reported
from ...log import log_to_stderr


def main(argv: list[str] | None = None) -> int:
    log_to_stderr()
    ap = argparse.ArgumentParser(prog="perfrepair.data_handler.inbound", description=__doc__)
    add_device_results_arg(ap)
    add_config_arg(ap)
    a = ap.parse_args(argv)
    return reported(lambda: _inbound(ap, a))


def _inbound(ap: argparse.ArgumentParser, a: argparse.Namespace) -> None:
    fill_device_results(ap, a)
    for line in write_inbound(a.device_results):
        print(line)


if __name__ == "__main__":
    sys.exit(main())
