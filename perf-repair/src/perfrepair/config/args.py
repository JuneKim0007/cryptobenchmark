"""--perfrepair-config on a command; one settings load per invocation; unset arguments filled from it."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any, Mapping

from .dotenv import load_env
from .load import Loaded, load
from .settings import ConfigError, Invalid, check_positive


def positive_int(text: str) -> int:
    """The argparse type of --turns, --sessions, --limit: the check their perfrepair.yaml keys get."""
    try:
        value = int(text)
        check_positive("value", value)
    except (ValueError, Invalid):
        raise argparse.ArgumentTypeError(f"{text!r} is not a positive integer") from None
    return value


def add_config_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--perfrepair-config", type=Path, metavar="FILE",
                        help="settings file; default: $PERFREPAIR_CONFIG, then perf-repair/perfrepair.yaml")


def load_settings(parser: argparse.ArgumentParser, args: argparse.Namespace) -> Loaded:
    try:
        return load(args.perfrepair_config, os.environ, load_env())
    except ConfigError as e:
        parser.error(str(e))


def fill(loaded: Loaded, args: argparse.Namespace, values: Mapping[str, tuple[str, Any]]) -> None:
    """values: argument dest → (settings key, code default)."""
    for dest, (key, default) in values.items():
        setattr(args, dest, loaded.value(key, getattr(args, dest), default))


def require(parser: argparse.ArgumentParser, args: argparse.Namespace, dest: str, key: str) -> None:
    if getattr(args, dest) is None:
        parser.error(f"the following arguments are required: --{dest} (or {key} in perfrepair.yaml)")
