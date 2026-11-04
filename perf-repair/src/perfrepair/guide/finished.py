"""The inputs an app ran with: the same inputs on a later run of the targets need no step (run_dir/run_record.py)."""
from __future__ import annotations

from pathlib import Path

from ..ai.suggest.site_replace.kind import charter
from ..app.find.sources import BUILD_NAMES, CATALOG, walk
from ..files import sha256_file, sha256_text
from ..run_dir import MEASUREMENTS, ROWS, GroupingPaths
from ..source.language import SOURCE_SUFFIXES
from .app_steps import measured_config
from .state import Guide

PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
# the code that turns an app tree into scopes, dossiers, edits and a measured harness: a change reruns the app
SCOPER = ("app", "scope", "source", "result", "repair")
HARNESS = ("scripts/scope/*.py", "scripts/scope_generate.py", "modules/android/src/androidTest/**/Scope*.kt")


def scoper_version() -> str:
    files = sorted(p for name in SCOPER for p in (PACKAGE / name).rglob("*") if p.suffix in (".py", ".yaml"))
    files += sorted(p for pattern in HARNESS for p in REPO.glob(pattern))
    return sha256_text("\n".join(f"{p.relative_to(REPO)} {sha256_file(p)}" for p in files))


def _tree_digest(g: Guide) -> str:
    named = (BUILD_NAMES + (CATALOG,))
    files = [p for p in walk(g.app_root) if p.suffix in SOURCE_SUFFIXES or p.name in named]
    return sha256_text("\n".join(f"{p.relative_to(g.app_root)} {sha256_file(p)}" for p in files))


def inputs(g: Guide, measured: bool) -> dict:
    return {"tree": _tree_digest(g), "scopes": sha256_file(g.paths.scopes), "units": sha256_file(g.paths.units), "scoper": scoper_version(),
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

