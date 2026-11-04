"""The inputs an app ran with: the same inputs on a later run of the targets need no step (run_dir/run_record.py)."""
from __future__ import annotations

from pathlib import Path

from ..ai.suggest.site_replace.kind import charter
from ..app.find.sources import BUILD_NAMES, CATALOG, walk
from ..data_handler.outbound.benchmark_runner import BenchmarkRunError, identify
from ..files import sha256_file, sha256_text
from ..run_dir import MEASUREMENTS, ROWS, GroupingPaths
from ..source.language import SOURCE_SUFFIXES
from ..stop.halt import Coded
from .app_steps import measured_config
from .state import Guide

PACKAGE = Path(__file__).resolve().parents[1]
# the code that turns an app tree into scopes, dossiers, edits and a harness.yaml: a change reruns the app
SCOPER = ("app", "scope", "source", "result", "repair")


def _scoper_files(name: str) -> list[Path]:
    # a renamed package would silently leave the digest, and no app would rerun
    files = sorted(p for p in (PACKAGE / name).rglob("*") if p.suffix in (".py", ".yaml"))
    if not files:
        raise Coded(f"missing_file: {PACKAGE / name} holds no scoper code; finished.SCOPER names it")
    return files


def scoper_version() -> str:
    files = [p for name in SCOPER for p in _scoper_files(name)]
    return sha256_text("\n".join(f"{p.relative_to(PACKAGE)} {sha256_file(p)}" for p in files))


def _harness_version(g: Guide) -> str:
    digest = identify(g.config or g.base_config, g.on_device).get("harness")
    if not digest:
        raise BenchmarkRunError("identify_failed: pipeline --identify reports no harness digest; is CRYPTOBENCH_ROOT an older checkout?")
    return digest


def code_versions(g: Guide) -> dict:
    return {"scoper": scoper_version(), "harness": _harness_version(g)}


def _tree_digest(g: Guide) -> str:
    named = (BUILD_NAMES + (CATALOG,))
    files = [p for p in walk(g.app_root) if p.suffix in SOURCE_SUFFIXES or p.name in named]
    return sha256_text("\n".join(f"{p.relative_to(g.app_root)} {sha256_file(p)}" for p in files))


def inputs(g: Guide, measured: bool) -> dict:
    return {"tree": _tree_digest(g), "scopes": sha256_file(g.paths.scopes), "units": sha256_file(g.paths.units), **g.code_versions,
            "groups": sha256_file(GroupingPaths(g.device).groups),
            "rows": sha256_file(g.device / ROWS), "measurements": sha256_file(g.device / MEASUREMENTS),
            "screening": g.catalog.sha256, "replace": charter(g.library).fingerprint, "perfMode": g.mode.name, "measured": measured,
            "maxChange": g.max_change, **_measured_with(g, measured)}


def _measured_with(g: Guide, measured: bool) -> dict:
    """A measured app also ran on its harness config: another config is another measurement."""
    if not measured:
        return {}
    config = measured_config(g)
    return {"benchmarkConfig": sha256_file(config) if config else None}

