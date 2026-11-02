from __future__ import annotations

from pathlib import Path

from ... import run_dir as rd
from ...dto import BenchmarkManifest
from ...files import read_yaml


def read_manifest(path: Path) -> tuple[BenchmarkManifest, Path]:
    path = Path(path)
    if not path.is_file():
        raise ValueError(rd.not_device_results(path.parent))
    doc = read_yaml(path)
    return BenchmarkManifest.from_json(doc), path.parent.resolve()


def manifest_file(manifest: BenchmarkManifest, base: Path, key: str) -> Path | None:
    rel = manifest.files.get(key)
    if rel is None:
        return None
    if not isinstance(rel, str):
        raise TypeError(f"manifest files.{key} is a list; read it with manifest.files[{key!r}]")
    path = (Path(base) / rel).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"manifest files.{key} = {rel} does not exist under {base}")
    return path
