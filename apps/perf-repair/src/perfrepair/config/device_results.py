"""Which device folder a command works on: --device-results, else --results-root with device.id or its only device."""
from __future__ import annotations

import argparse
import functools
import logging
import tempfile
from pathlib import Path

from cryptobench.paths import Results, RunTree
from cryptobench.paths import DEVICE, MANIFEST, MEASUREMENTS, PRIMITIVES, ROWS, RUN_LOG
from .. import run_dir as rd
from ..inputs.table import DEVICE_ID
from ..stop.halt import Coded
from .args import load_settings
from .load import Loaded

LOG = logging.getLogger(__name__)
TEMP_ROOTS = ("/tmp", "/var/tmp", "/var/folders")
HELP = "the device's results folder, <results root>/<device id>; default: --results-root, with device.id when it holds several"


def add_device_results_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--device-results", type=Path, help=HELP)
    parser.add_argument("--results-root", type=Path, metavar="DIR", help="the results root, <DIR>/<device id>")


def select_device(root: Path, wanted: str | None) -> Path:
    found = Results(root).devices()
    if wanted and wanted not in found:
        raise Coded(f"device_not_in_results: {wanted}; {root} holds {found}")
    if not found:
        raise Coded(f"no_device_results: {root} holds no <device id>/{MANIFEST}; run the benchmark")
    if not wanted and len(found) > 1:
        raise Coded(f"several_device_results: {root} holds {', '.join(found)}; set device.id or pass --device-results")
    return root / (wanted or found[0])


# cached: a guide calling other commands in-process still warns once
@functools.lru_cache(maxsize=None)
def _warn_if_temp(folder: Path) -> None:
    real = folder.resolve()
    if any(real.is_relative_to(Path(root).resolve()) for root in (*TEMP_ROOTS, tempfile.gettempdir())):
        LOG.warning("results_in_temp: %s is under a temporary folder the system may wipe; keep results elsewhere", folder)


def _results_root(parser: argparse.ArgumentParser, args: argparse.Namespace) -> Path:
    if args.results_root is None:
        parser.error("the following arguments are required: --device-results (or --results-root)")
    return args.results_root.expanduser()


def device_root(parser: argparse.ArgumentParser, args: argparse.Namespace, loaded: Loaded) -> Path | None:
    """The results root when the caller makes the device folder itself (probe_device); None when one is named."""
    if args.device_results is not None or loaded.read(DEVICE_ID):
        fill_device_results(parser, args, loaded)
        return None
    root = _results_root(parser, args)
    _warn_if_temp(root)
    return root


# a benchmark that did not end removed the manifest first; these files of the earlier run stay behind
STAGE_FILES = (DEVICE, ROWS, MEASUREMENTS, RUN_LOG, PRIMITIVES)


def _unfinished(folder: Path) -> bool:
    return not (RunTree(folder).manifest).is_file() and any((folder / f).exists() for f in STAGE_FILES)


def fill_device_results(parser: argparse.ArgumentParser, args: argparse.Namespace, loaded: Loaded | None = None) -> None:
    if args.device_results is None:
        loaded = loaded or load_settings(parser, args)
        args.device_results = select_device(_results_root(parser, args), loaded.read(DEVICE_ID))
    args.device_results = args.device_results.expanduser()
    if Results(args.device_results).devices() or _unfinished(args.device_results):
        raise Coded(rd.not_device_results(args.device_results))
    _warn_if_temp(args.device_results)
