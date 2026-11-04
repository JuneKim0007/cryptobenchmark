"""A delta: only the gaps and their anchors, measured by the same pipeline with the stored setup, then checked and merged
add-only; a setup that differs or anchors that drift are said in one line each, never merged silently."""
from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .. import run_dir as rd
from ..data_handler.inbound import (
    manifest_file,
    read_manifest,
    read_prepared,
    read_results,
)
from ..data_handler.outbound.benchmark_runner import identify, run_pipeline
from ..dto.benchmark_coverage import (
    CHECKED,
    LOST,
    METRIC_MISSING,
    PARTIAL,
    UNCHECKED,
    Gap,
)
from ..dto.dossier import SETUP_DRIFT
from ..files import read_json, read_yaml, write_text_making_parents
from ..result.estimate import compare
from ..result.gain import UNCHANGED, change_of
from ..stop.halt import Coded
from .delta_config import DELTA, narrowed, write_delta_config, write_rerun_config
from .delta_estimate import estimate_line, planned_cases, seconds_per_case
from .delta_merge import merge_delta
from .setup_fingerprint import (
    before_measuring,
    case_setups,
    differing,
    fingerprint,
    without_narrowed,
)

RESULTS = "results"
BASELINE_ENV = "CRYPTOBENCH_THERMAL_BASELINE"
DRIFT_METRIC = "timeNs"


@dataclass(frozen=True)
class Delta:
    """mismatch: the setup fields that differ, nothing merged; drift: anchor lines past the noise rule; compared: the
    cases measured in both sessions, 0 leaving the delta unchecked."""
    session: str
    cases: tuple[str, ...] = ()
    anchors: tuple[str, ...] = ()
    mismatch: tuple[str, ...] = ()
    drift: tuple[str, ...] = ()
    lines: list[str] = field(default_factory=list)
    compared: int = 0

    @property
    def comparison(self) -> str:
        return SETUP_DRIFT if self.drift else CHECKED if self.compared else UNCHECKED

    def summary(self) -> dict:
        return {"session": self.session, "added": list(self.cases), "anchors": list(self.anchors),
                "mismatch": list(self.mismatch), "comparison": self.comparison, "drift": list(self.drift)}


def _stored_baseline(folder: Path) -> str | None:
    """The stored run's thermal gate baseline, so the delta waits for the same target."""
    for path in sorted((Path(folder) / "benchmark").rglob("thermal.json")):
        gate = read_json(path).get("gate") or {}
        if gate.get("baseline") is not None:
            return str(gate["baseline"])
    return None


def _measurements(folder: Path) -> dict:
    manifest, base = read_manifest(folder / rd.MANIFEST)
    processes = [(base / p).resolve() for p in manifest.files.get("processes") or []]
    prepared = read_prepared(manifest_file(manifest, base, "prepared"))
    return read_results(manifest_file(manifest, base, "benchmark"), prepared, processes)[1]


def _drift(stored: dict, now: dict, anchors: set[str]) -> tuple[tuple[str, ...], int]:
    """Each anchor case whose change is beyond noise and past improvingRatio (result/gain.py); how many both sessions hold."""
    out, compared = [], 0
    for cid in sorted(anchors):
        before, after = (stored.get(cid) or {}).get(DRIFT_METRIC), (now.get(cid) or {}).get(DRIFT_METRIC)
        if before and after:
            compared += 1
            c = compare(before, after)
            if change_of(c.ratio, c.pImprove) != UNCHANGED:
                out.append(f"{cid}: {DRIFT_METRIC} ratio {c.ratio:.3f}, pImprove {c.pImprove}")
    return tuple(out), compared


def _whole_run_cases(folder: Path, measured: int) -> int:
    """The cases the whole benchmark's took: line timed: the measured count without what deltas added."""
    return measured - sum(len(d.get("cases") or ()) for d in read_yaml(folder / rd.MANIFEST).get("deltas") or ())


def _case_mismatch(stored: Path, staged: Path, shared: set[str]) -> list[str]:
    mine, theirs = case_setups(stored), case_setups(staged)
    return [f"case {cid}.{line}" for cid in sorted(shared) for line in differing(mine.get(cid, {}), theirs.get(cid, {}))]


def _retried(gaps: tuple[Gap, ...]) -> list[str]:
    return sorted({g.case for g in gaps if g.gap == LOST})


def _fill(gaps: tuple[Gap, ...]) -> dict[str, list[str]]:
    """Per stored case with rows, the metrics a partial gap found missing."""
    out: dict[str, list[str]] = {}
    for g in gaps:
        if g.gap == PARTIAL and g.case and g.reason.startswith(METRIC_MISSING):
            out.setdefault(g.case, []).append(g.metric)
    return out


def run_delta(folder: Path, gaps: tuple[Gap, ...], anchors: frozenset[str], session: str, on_device: bool,
              echo: Callable[[str], None], benchmark: Path | str | None = None) -> Delta:
    folder = Path(folder)
    manifest, _ = read_manifest(folder / rd.MANIFEST)
    stored_config = Path(manifest.config)
    identity = identify(stored_config if stored_config.is_file() else None, on_device, benchmark)
    if identity["deviceId"] != folder.name:
        raise Coded(f"device_id_changed: the connected device is {identity['deviceId']}, the folder is {folder.name}; "
                    "a delta measures the device the benchmark did")
    items = {g.item for g in gaps}
    run = narrowed((read_yaml(stored_config).get("run") or {}) if stored_config.is_file() else {}, gaps)
    config = write_delta_config(stored_config, folder, items | anchors, run)
    alike = without_narrowed if run is not None else (lambda a, b: (a, b))
    planned = {}
    for c in (read_prepared(manifest_file(manifest, folder, "prepared")) or {}).values():
        planned[f"{c['type']}|{c['algorithm']}|{c['provider']}"] = planned.get(f"{c['type']}|{c['algorithm']}|{c['provider']}", 0) + 1
    line = estimate_line(planned_cases(gaps, anchors, planned), len(items), len(anchors),
                         seconds_per_case(folder, _whole_run_cases(folder, manifest.counts.get("measured", 0))))
    echo(line)
    root = folder / DELTA / RESULTS
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    baseline = _stored_baseline(folder)
    stage = "device" if on_device else "bench"
    staged = root / folder.name
    # a setup that differs is refused before the session, not after hours of it
    run_pipeline(config, root, "device" if on_device else "configure", benchmark=benchmark, echo=echo, device=folder,
                 extra=("--probe",))
    early = tuple(before_measuring(*alike(fingerprint(folder), fingerprint(staged))))
    if early:
        return Delta(session, mismatch=early, lines=[line])
    run_pipeline(config, root, stage, benchmark=benchmark, echo=echo, device=folder,
                 extra=() if on_device else ("--discovery", "reuse"), env={BASELINE_ENV: baseline} if baseline else None)
    stored_cases = {c["id"] for c in read_json(folder / manifest.files["benchmark"]).get("cases") or []}
    staged_doc = read_json(staged / read_manifest(staged / rd.MANIFEST)[0].files["benchmark"])
    staged_cases = {c["id"] for c in staged_doc.get("cases") or []}
    shared = stored_cases & staged_cases
    mismatch = tuple(differing(*alike(fingerprint(folder), fingerprint(staged))) + _case_mismatch(folder, staged, shared))
    if mismatch:
        return Delta(session, anchors=tuple(sorted(shared)), mismatch=mismatch, lines=[line])
    drift, compared = _drift(rd.load_measurements(folder).byRow, _measurements(staged), shared)
    added = staged_cases - stored_cases
    done = Delta(session, tuple(sorted(added)), tuple(sorted(shared)), (), drift, [line], compared)
    merge_delta(folder, staged, added, session, done.comparison, _retried(gaps), _fill(gaps))
    return done


def rerun_whole(folder: Path, gaps: tuple[Gap, ...], session: str, on_device: bool, echo: Callable[[str], None],
                benchmark: Path | str | None = None) -> None:
    """Only with device.benchmark.onSetupMismatch rerun: the stored config, the gaps added, measured whole into the folder;
    listed among the deltas, since every dossier may have changed."""
    folder = Path(folder)
    manifest, _ = read_manifest(folder / rd.MANIFEST)
    config = write_rerun_config(Path(manifest.config), folder, {g.item for g in gaps})
    run_pipeline(config, folder.parent, "device" if on_device else "bench", benchmark=benchmark, echo=echo, device=folder)
    measured = read_yaml(folder / rd.MANIFEST)
    write_text_making_parents(folder / rd.MANIFEST, yaml.safe_dump({**measured, "retried": _retried(gaps), "deltas": [
        {"session": session, "cases": [], "rerun": True}]}, sort_keys=False))
