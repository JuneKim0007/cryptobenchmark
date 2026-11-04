"""The benchmark gate, before any model call at its point (after the used set, after grouping): every used item measured or
a coded gap; the gaps a delta can close measured once, then checked again; a gap left stops `not_benchmarked`."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .. import run_dir as rd
from ..dto.benchmark_coverage import GAP_DELTA, GAP_STOP, LOST, SETUP_RERUN, SETUP_STOP, UNCHECKED, Coverage, Gap
from ..dto.grouping import read_items
from ..dto.perf_mode import PerfMode
from ..dto.used import UsedSet
from ..files import read_json
from ..log import run_id, step
from ..stop import terminate
from .benchmark_coverage import CoverageFile
from .delta import Delta, rerun_whole, run_delta
from .gate_after import rebuilt
from .measured_check import measured_check

UNLOCKED = " (drift is unreliable on a host: its clocks are not locked)"


@dataclass(frozen=True)
class GatePolicy:
    """command: what to run instead when this run cannot measure (--device-results); None: it can."""
    on_gap: str = GAP_DELTA
    on_mismatch: str = SETUP_STOP
    command: str | None = None


def anchors(folder: Path, used: UsedSet, gaps: tuple[Gap, ...]) -> frozenset[str]:
    """The comparators of each gap: used items of its family sharing an app with it, measured already."""
    items = {i.qualified: i for i in read_items(read_json(rd.GroupingPaths(folder).items))}
    apps = {u.item: set(u.apps) for u in used.items}
    missing = {g.item for g in gaps}
    return frozenset(u.item for u in used.items for g in missing if u.item not in missing and u.item in items
                     and g in items and items[u.item].family == items[g].family and apps[u.item] & apps.get(g, set()))


def _listed(gaps: tuple[Gap, ...]) -> str:
    return "; ".join(f"{g.item} {g.operation} {g.variant} k{g.keySize} i{g.inputSize} {g.metric}: {g.gap} ({g.reason})"
                     for g in gaps)


def _stop(gaps: tuple[Gap, ...], why: str, next_step: str | None = None) -> None:
    terminate("not_benchmarked", f"{len(gaps)} gaps {why}: {_listed(gaps)}", stage="device", step="gate",
              data={"gaps": len(gaps)}, next_step=next_step)


def _said(delta: Delta, had_anchors: bool, echo: Callable[[str], None]) -> None:
    for line in delta.drift:
        echo(f"device gate: setup_drift: {line}")
    if delta.drift:
        echo(f"device gate: setup_drift: comparisons across session {delta.session} are not sent as estimates; a whole "
             "rerun in one session is your choice")
    if delta.comparison == UNCHECKED and not delta.mismatch:
        why = "the overrides leave its anchors no case shared with the stored run" if had_anchors else "its gaps have no anchor"
        echo(f"device gate: unchecked: delta {delta.session}: {why}, so nothing says its session agrees with the stored one; "
             "its estimates carry cross_session")


def benchmark_gate(folder: Path, point: str, used: UsedSet, perf: PerfMode, policy: GatePolicy, on_device: bool,
                   echo: Callable[[str], None], benchmark: Path | str | None = None,
                   file: CoverageFile | None = None) -> tuple[Coverage, bool]:
    """The coverage left and whether a delta merged; a stop ends through terminate."""
    folder, file = Path(folder), file or CoverageFile()
    with step("device", "gate", detail=point) as s:
        first = measured_check(folder, used.names, perf)
        file.write(folder, point, first)
        s.count(**{k: v for k, v in first.totals().items() if v})
        echo(f"device gate ({point}): {first.totals()['itemsMeasured']} of {len(used.names)} used items measured, "
             f"{len(first.delta())} gaps to measure, {len(first.coded())} coded")
        if not first.delta():
            return first, False
        if policy.command:
            _stop(first.delta(), f"and --device-results cannot measure them; run {policy.command}", policy.command)
        if policy.on_gap == GAP_STOP:
            _stop(first.delta(), "and device.benchmark.onGap is stop")
        comparators = anchors(folder, used, first.delta())
        delta = run_delta(folder, first.delta(), comparators, f"{run_id()}-{point}", on_device, echo, benchmark)
        _said(delta, bool(comparators), echo)
        if delta.mismatch and policy.on_mismatch == SETUP_RERUN:
            echo(f"device gate: setup_mismatch: {delta.mismatch[0]}; device.benchmark.onSetupMismatch rerun: the whole "
                 "benchmark is measured again")
            rerun_whole(folder, first.delta(), on_device, echo, benchmark)
        elif delta.mismatch:
            terminate("setup_mismatch", f"the delta was measured under another setup, nothing merged: {delta.mismatch[0]}"
                      + (f" (and {len(delta.mismatch) - 1} more)" if len(delta.mismatch) > 1 else ""),
                      stage="device", step="gate", data={"fields": list(delta.mismatch)})
        rebuilt(folder, frozenset(g.item for g in first.delta()), echo)
        lost = {g.key for g in first.delta() if g.gap == LOST}
        after = measured_check(folder, used.names, perf, lost)
        file.write(folder, point, after, delta.summary())
        echo(f"device gate ({point}): delta {delta.session}: {len(delta.cases)} cases added, {len(delta.anchors)} anchor "
             f"cases, {len(delta.drift)} drifted, {delta.comparison}{'' if on_device else UNLOCKED}; "
             f"{after.totals()['itemsMeasured']} of {len(used.names)} used items measured")
        if after.delta():
            _stop(after.delta(), "left after one delta")
        return after, True
