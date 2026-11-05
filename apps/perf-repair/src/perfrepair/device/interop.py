"""The pair check before options: the plan of the pairs app sites reach, verdicts of the same setup kept, the rest run by
pipeline.py --interop on the benchmark's own target, imported, and groups.json reported again."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import yaml

from .. import run_dir as rd
from ..data_handler.inbound import manifest_file, read_manifest
from ..data_handler.outbound.benchmark_runner import require_connected, run_pipeline
from ..dto.interop import SCHEMA_VERSION, PairResult, PlannedPair, member_name, plan_document
from ..files import read_yaml, write_text
from ..grouping.interop_plan import plan_for, write_plan
from ..grouping.interop_read import imported, write_results
from ..grouping.report.checks import report
from ..run_dir import GroupingPaths
from .setup_fingerprint import provider_setup

DEVICE_MODE = "device"


@dataclass(frozen=True)
class Checked:
    """planned: the plan's pairs and those it holds back; pending: pairs with no verdict of this setup; ran: checked now."""
    planned: int
    reused: int
    pending: int
    ran: int
    results: tuple[PairResult, ...] = ()


def _kept(paths: GroupingPaths, setup: dict) -> dict[tuple, dict]:
    """A verdict holds for its setup and the key size it ran at."""
    doc = read_yaml(paths.interop) if paths.interop.exists() else {}
    if doc.get("setup") != setup:
        return {}
    return {(member_name(r["a"]), member_name(r["b"]), r.get("keySize")): r for r in doc.get("pairs") or []}


def unreachable(folder: Path, on_device: bool) -> str | None:
    """Why this run cannot run the oracle on the folder's target; None when it can."""
    manifest, _ = read_manifest(folder / rd.MANIFEST)
    if manifest.mode == DEVICE_MODE and not on_device:
        return "a device folder's pairs need --device or apps.measure"
    return None if Path(manifest.config).is_file() else f"the config the benchmark ran with is gone: {manifest.config}"


def _oracle(folder: Path, plan: Path, echo: Callable[[str], None]) -> dict[int, dict]:
    """The benchmark's own config and mode, so the check sees the providers it measured."""
    manifest, _ = read_manifest(folder / rd.MANIFEST)
    config, on_device = Path(manifest.config), manifest.mode == DEVICE_MODE
    require_connected(folder, config, on_device, "the pair check runs on the device the benchmark did")
    run_pipeline(config, folder.parent, "device" if on_device else "bench", echo=echo, extra=("--interop", str(plan)),
                 device=folder)
    rd.vouch_manifest(folder)
    manifest, base = read_manifest(folder / rd.MANIFEST)
    return {int(r["id"]): r for r in read_yaml(manifest_file(manifest, base, "interop")).get("pairs") or []}


def check_pairs(folder: Path, sites: frozenset[str] | None, run: bool, echo: Callable[[str], None]) -> Checked:
    """run False: no oracle runs, and pending says how many pairs still need one; an unchanged rerun writes nothing."""
    paths, setup = GroupingPaths(folder), provider_setup(folder)
    kept = _kept(paths, setup)
    document = plan_for(paths, sites)
    planned = [PlannedPair.from_json(p) for p in document["pairs"]]
    held_back = len(document.get("notCheckable") or ())
    todo = [p for p in planned if (p.a, p.b, p.keySize) not in kept]
    if todo and not run:
        _drop_other_setup(paths, setup)
        return Checked(len(planned) + held_back, len(planned) - len(todo), len(todo), 0)
    fresh = _run(folder, paths, todo, echo) if todo else {}
    # a pair the oracle left out is missing here, and write_results refuses the ids
    rows = [{**fresh[p.id], "keySize": p.keySize} if p.id in fresh else {**kept[(p.a, p.b, p.keySize)], "id": p.id, "group": p.group}
            for p in planned if p.id in fresh or (p.a, p.b, p.keySize) in kept]
    results = {"schemaVersion": SCHEMA_VERSION, "setup": setup, "pairs": rows}
    if fresh or not _current(paths, document, results):
        write_plan(paths, sites)
        write_results(paths, results)
        report(paths)
    return Checked(len(planned) + held_back, len(planned) - len(todo), 0, len(todo), tuple(imported(paths)))


def _drop_other_setup(paths: GroupingPaths, setup: dict) -> None:
    """Verdicts of another setup must not stay on the options; a hand import names no setup and stays."""
    if paths.interop.exists() and read_yaml(paths.interop).get("setup") not in (None, setup):
        paths.interop.unlink()
        report(paths)


def _current(paths: GroupingPaths, document: dict, results: dict) -> bool:
    return all(f.exists() for f in (paths.interop_plan, paths.interop)) and read_yaml(paths.interop_plan) == document \
        and read_yaml(paths.interop) == results


def _run(folder: Path, paths: GroupingPaths, todo: list[PlannedPair], echo: Callable[[str], None]) -> dict[int, dict]:
    write_text(paths.interop_pending, yaml.safe_dump(plan_document(todo), sort_keys=False))
    try:
        return _oracle(folder, paths.interop_pending, echo)
    finally:
        paths.interop_pending.unlink(missing_ok=True)
