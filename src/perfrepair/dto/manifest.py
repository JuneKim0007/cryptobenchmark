"""results/manifest.yaml — what one cryptobenchmark run wrote, and where.

Written by cryptobenchmark's scripts/pipeline.py at the end of every run; read by
perfrepair.data_handler.inbound.manifest. Paths are relative to the manifest's own directory,
so a results directory can be moved or archived whole.

    schemaVersion: 1
    mode: host | device
    config: <path of the global.yaml the run used>
    runtime: {...}                      # benchmark.json's runtime block; the probe's when not measured
    providers:                          # from the probe, in precedence order
    - {name: X, precedence: 1, serviceCount: 105}
    files:                              # a stage that did not run is absent, never null
      probe: discovery/probe_<utc>.yaml
      trial: discovery/trial_<utc>.yaml
      inventory: configuration/inventory.yaml
      effective: configuration/effective.yaml
      prepared: preparation/prepared.yaml
      skipped: preparation/skipped.yaml
      benchmark: benchmark/benchmark.json
      processes: [benchmark/process-1/benchmark.json, ...]   # only when processRepetitions > 1
    counts: {prepared: n, skipped: n, measured: n}
"""
from __future__ import annotations

from dataclasses import dataclass, field

SCHEMA_VERSION = 1
MODES = ("host", "device")


@dataclass(frozen=True)
class ProviderEntry:
    name: str
    precedence: int
    serviceCount: int


@dataclass
class BenchmarkManifest:
    mode: str
    config: str
    runtime: dict
    providers: list[ProviderEntry]
    files: dict[str, str | list[str]]
    counts: dict[str, int] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {"schemaVersion": SCHEMA_VERSION, "mode": self.mode, "config": self.config,
                "runtime": self.runtime,
                "providers": [vars(p) for p in self.providers],
                "files": self.files, "counts": self.counts}

    @classmethod
    def from_json(cls, doc: dict) -> "BenchmarkManifest":
        if doc.get("schemaVersion") != SCHEMA_VERSION:
            raise ValueError(f"manifest schemaVersion {doc.get('schemaVersion')} is not {SCHEMA_VERSION}")
        if doc.get("mode") not in MODES:
            raise ValueError(f"manifest mode {doc.get('mode')!r} is not one of {MODES}")
        return cls(doc["mode"], doc.get("config", ""), doc.get("runtime") or {},
                   [ProviderEntry(p["name"], int(p["precedence"]), int(p.get("serviceCount", 0)))
                    for p in doc.get("providers") or []],
                   doc.get("files") or {}, doc.get("counts") or {})
