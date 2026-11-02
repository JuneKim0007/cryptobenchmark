"""Which device folder a command works on: --device-results, else paths.results with device.id or its only device."""
from __future__ import annotations

import argparse
import functools
import logging
import tempfile
from pathlib import Path

from .. import run_dir as rd
from ..inputs.table import DEVICE_ID, PATHS_RESULTS
from .args import load_settings
from .load import Loaded

LOG = logging.getLogger(__name__)
TEMP_ROOTS = ("/tmp", "/var/tmp", "/var/folders")
HELP = "the device's results folder, <results root>/<device id>; default: paths.results, with device.id when it holds several"


def add_device_results_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--device-results", type=Path, help=HELP)


def select_device(root: Path, wanted: str | None) -> Path:
    found = rd.device_folders(root)
    if wanted and wanted not in found:
        raise ValueError(f"device_not_in_results: {wanted}; {root} holds {found}")
    if not found:
        raise ValueError(f"no_device_results: {root} holds no <device id>/{rd.MANIFEST}; run the benchmark")
    if not wanted and len(found) > 1:
        raise ValueError(f"several_device_results: {root} holds {', '.join(found)}; set device.id or pass --device-results")
    return root / (wanted or found[0])


# cached: a guide calling other commands in-process still warns once
@functools.lru_cache(maxsize=None)
def _warn_if_temp(folder: Path) -> None:
    real = folder.resolve()
    if any(real.is_relative_to(Path(root).resolve()) for root in (*TEMP_ROOTS, tempfile.gettempdir())):
        LOG.warning("results_in_temp: %s is under a temporary folder the system may wipe; keep results elsewhere", folder)


def fill_device_results(parser: argparse.ArgumentParser, args: argparse.Namespace, loaded: Loaded | None = None) -> None:
    if args.device_results is None:
        loaded = loaded or load_settings(parser, args)
        root = loaded.read(PATHS_RESULTS)
        if root is None:
            parser.error(f"the following arguments are required: --device-results (or {PATHS_RESULTS.key} in perfrepair.yaml)")
        args.device_results = select_device(Path(root).expanduser(), loaded.read(DEVICE_ID))
    args.device_results = args.device_results.expanduser()
    _warn_if_temp(args.device_results)
