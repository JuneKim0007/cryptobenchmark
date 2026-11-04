"""The guide's two benchmark gate points: after the used set and after grouping, each before the next model call."""
from __future__ import annotations

from .. import run_dir as rd
from ..data_handler.inbound import read_manifest
from ..device.benchmark_coverage import clear_coverage
from ..device.gate import GatePolicy, benchmark_gate
from ..device.missing_rows import coverage_rows
from ..device.used import write_used
from ..inputs.table import BENCHMARK_ON_GAP, BENCHMARK_ON_SETUP_MISMATCH
from ..run_dir import GroupingPaths
from .state import Guide

USED, GROUPED = "used", "grouped"


def rerun_command(g: Guide) -> str:
    """--device-results names a folder, not a config: the command that measures it with its own device stage."""
    manifest, _ = read_manifest(g.device / rd.MANIFEST)
    device = " --device" if manifest.mode == "device" else ""
    return (f"`python3 -m perfrepair guide --config {manifest.config}{device} --results-root {g.device.parent}` with "
            "device.id unset, so the guide makes the device stage itself")


def _policy(g: Guide) -> GatePolicy:
    read = g.settings.read if g.settings else (lambda row: row.default)
    return GatePolicy(read(BENCHMARK_ON_GAP), read(BENCHMARK_ON_SETUP_MISMATCH), rerun_command(g) if g.root is None else None)


def gate(g: Guide, point: str, perf) -> None:
    """Its own line; nothing without the used set (device.filterByApps off); after grouping the set is made again from
    today's groups."""
    used = rd.load_used(g.device)
    if used is None or not GroupingPaths(g.device).items.is_file():
        clear_coverage(g.device)
        return
    if point == GROUPED:
        used = write_used(g.device, sorted(used.apps))
    coverage, merged = benchmark_gate(g.device, point, used, perf, _policy(g), g.on_device, g.echo, file=g.coverage)
    g.missing.put(f"coverage {point}", coverage_rows(g.device, coverage, used))
    g.delta_merged = g.delta_merged or merged
