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
