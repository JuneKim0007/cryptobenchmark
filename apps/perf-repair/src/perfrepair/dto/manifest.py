from __future__ import annotations

from dataclasses import dataclass, field

from cryptobench.catalogue.document import DocumentKind
from .units import DisplayUnits

SCHEMA_VERSION = 1
MANIFEST_DOC = DocumentKind("manifest", SCHEMA_VERSION)
MODES = ("host", "device")


def _operations(value) -> dict[str, tuple[str, ...]] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or not all(isinstance(v, list) for v in value.values()):
        raise ValueError("invalid: manifest operations, a map of engine type to its operations")
    return {str(t): tuple(map(str, ops)) for t, ops in value.items()}


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
    deviceId: str = ""
    # digests of providers.bundled and global.yaml the run used; empty from a pipeline before they were recorded
    inputs: dict[str, str] = field(default_factory=dict)
    units: DisplayUnits = DisplayUnits()
    # per engine type the operations the harness times; None from a benchmark before it recorded them
    operations: dict[str, tuple[str, ...]] | None = None

    def operations_of(self, engine_type: str) -> tuple[str, ...] | None:
        """Empty: the type falls back to TYPE_DEFAULT, whose invocation times nothing; None: not recorded."""
        if self.operations is None:
            return None
        return {t.upper(): ops for t, ops in self.operations.items()}.get(engine_type.upper(), ())

    def to_json(self) -> dict:
        return {"schemaVersion": SCHEMA_VERSION, "mode": self.mode, "config": self.config, "deviceId": self.deviceId,
                "runtime": self.runtime,
                "providers": [vars(p) for p in self.providers],
                "files": self.files, "counts": self.counts, "inputs": self.inputs, "units": self.units.to_json(),
                **({"operations": {t: list(o) for t, o in self.operations.items()}} if self.operations is not None else {})}

    @classmethod
    def from_json(cls, doc: dict) -> "BenchmarkManifest":
        MANIFEST_DOC.check(doc)
        if doc.get("mode") not in MODES:
            raise ValueError(f"manifest mode {doc.get('mode')!r} is not one of {MODES}")
        if not doc.get("deviceId"):
            raise ValueError("manifest_without_device_id; rerun the benchmark")
        return cls(doc["mode"], doc.get("config", ""), doc.get("runtime") or {},
                   [ProviderEntry(p["name"], int(p["precedence"]), int(p.get("serviceCount", 0)))
                    for p in doc.get("providers") or []],
                   doc.get("files") or {}, doc.get("counts") or {}, doc["deviceId"],
                   doc.get("inputs") or {}, DisplayUnits.parse(doc.get("units")), _operations(doc.get("operations")))
