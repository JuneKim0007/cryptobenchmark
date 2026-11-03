"""--perfrepair-config on a command; one settings load per invocation; unset arguments filled from it."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Mapping

from ..dto.perf_mode import PerfMode
from ..inputs.check import Invalid, check_positive
from ..inputs.table import Row
from .dotenv import load_env
from .load import Loaded, load
from .settings import ConfigError
from .stops import install_stops


def positive_int(text: str) -> int:
    """The argparse type of --turns, --sessions, --limit: the check their perfrepair.yaml keys get."""
    try:
        value = int(text)
        check_positive("value", value)
    except (ValueError, Invalid):
        raise argparse.ArgumentTypeError(f"{text!r} is not a positive integer") from None
    return value


def perf_mode(text: str) -> str:
    """The argparse type of --perf-mode: `generic`, or keys joined by `,` (energy,latency,throughput)."""
    try:
        PerfMode.parse(text)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e)) from None
    return text


def add_config_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--perfrepair-config", type=Path, metavar="FILE",
                        help="settings file; default: $PERFREPAIR_CONFIG, then perf-repair/perfrepair.yaml")


def load_settings(parser: argparse.ArgumentParser, args: argparse.Namespace) -> Loaded:
    try:
        loaded = load(args.perfrepair_config, os.environ, load_env())
    except ConfigError as e:
        parser.error(str(e))
    install_stops(loaded)
    return loaded


def fill(loaded: Loaded, args: argparse.Namespace, rows: Mapping[str, Row]) -> None:
    """rows: argument dest → its row."""
    for dest, row in rows.items():
        setattr(args, dest, loaded.read(row, getattr(args, dest)))


def require(parser: argparse.ArgumentParser, args: argparse.Namespace, dest: str, row: Row) -> None:
    if getattr(args, dest) is None:
        parser.error(f"the following arguments are required: --{dest} (or {row.key} in perfrepair.yaml)")

