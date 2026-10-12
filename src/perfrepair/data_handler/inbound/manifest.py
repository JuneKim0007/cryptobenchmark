"""Where one cryptobenchmark run put its files: the only entry point into a results tree.

perf-repair never globs a results directory; it reads what the manifest lists and nothing else, so a
stage that did not run is visibly absent instead of silently replaced by an older file.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from ...dto import BenchmarkManifest


def read_manifest(path: Path) -> tuple[BenchmarkManifest, Path]:
    """(manifest, base directory its relative paths resolve against)."""
    path = Path(path)
    doc = yaml.safe_load(path.read_text()) or {}
    return BenchmarkManifest.from_json(doc), path.parent.resolve()


def manifest_file(manifest: BenchmarkManifest, base: Path, key: str) -> Path | None:
    """Absolute path of `files[key]`; None when the stage did not run.

    A listed file that is missing is an error: the manifest claims it was written."""
    rel = manifest.files.get(key)
    if rel is None:
        return None
    if not isinstance(rel, str):
        raise TypeError(f"manifest files.{key} is a list; read it with manifest.files[{key!r}]")
    path = (Path(base) / rel).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"manifest files.{key} = {rel} does not exist under {base}")
    return path
