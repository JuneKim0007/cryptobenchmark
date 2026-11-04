"""Composition root: the manifest read once; catalogs, probe and benchmark documents built on first use."""
from __future__ import annotations

from functools import cached_property
from pathlib import Path

from ...catalog.families import Families
from ...catalog.names import Names
from ...catalog.screening import Screening
from ...dto import BenchmarkManifest
from ...files import read_document
from .manifest import manifest_file, read_manifest
from .probe import Probe

PIECES = ("catalog", "names", "families", "screening", "probe", "trial", "inventory", "prepared", "benchmark")


class RunContext:

    def __init__(self, path: Path, manifest: BenchmarkManifest, base: Path, **given):
        unknown = sorted(set(given) - set(PIECES))
        if unknown:
            raise TypeError(f"run_context: unknown pieces {unknown}")
        self.path, self.manifest, self.base = Path(path), manifest, base
        # a given piece shadows the cached_property of its name
        vars(self).update({k: v for k, v in given.items() if v is not None})

    @classmethod
    def load(cls, manifest_path: Path, **given) -> "RunContext":
        manifest, base = read_manifest(manifest_path)
        return cls(manifest_path, manifest, base, **given)

    def file(self, key: str) -> Path | None:
        return manifest_file(self.manifest, self.base, key)

    def _required(self, key: str) -> Path:
        path = self.file(key)
        if path is None:
            raise FileNotFoundError(f"{self.path}: files.{key} is absent")
        return path

    @cached_property
    def catalog(self) -> Names:
        return Names.load()

    @cached_property
    def names(self) -> Names:
        return self.probe.names(self.catalog)

    @cached_property
    def families(self) -> Families:
        return Families.load()

    @cached_property
    def screening(self) -> Screening:
        return Screening.load(names=self.catalog)

    @cached_property
    def probe(self) -> Probe:
        return Probe.load(self._required("probe"))

    @cached_property
    def trial(self) -> dict:
        return read_document(self._required("trial"))

    @cached_property
    def inventory(self) -> dict:
        return read_document(self._required("inventory"))

    @cached_property
    def prepared(self) -> dict:
        return read_document(self._required("prepared"))

    @cached_property
    def benchmark(self) -> dict:
        return read_document(self._required("benchmark"))
