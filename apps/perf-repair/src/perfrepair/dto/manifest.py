from __future__ import annotations

from dataclasses import dataclass, field

from cryptobench.shared.results.manifest import MANIFEST_DOC, MODES
from cryptobench.shared.stats.units import DisplayUnits


def _operations(value) -> dict[str, tuple[str, ...]] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or not all(isinstance(v, list) for v in value.values()):
        raise ValueError("invalid: manifest operations, a map of engine type to its operations")
    return {str(t): tuple(map(str, ops)) for t, ops in value.items()}


def _units(value) -> dict:
    DisplayUnits.parse(value)
    return dict(value or {})


@dataclass(frozen=True)
class ProviderEntry:
    name: str
    precedence: int
    serviceCount: int


@dataclass
class BenchmarkManifest:
    """The runner's manifest (shared/results/manifest.py) and what a delta merge adds; to_json gives back the fields as written, in its order."""
    mode: str
    config: str
    runtime: dict
    providers: list[ProviderEntry]
    files: dict[str, str | list[str]]
    counts: dict[str, int] = field(default_factory=dict)
    deviceId: str = ""
    inputs: dict[str, str] = field(default_factory=dict)
    # analysis.units as written; absent: effective.yaml named none
    units: dict = field(default_factory=dict)
    # per engine type the operations the harness times
    operations: dict[str, tuple[str, ...]] | None = None
    energy: dict | None = None
    problems: tuple[str, ...] = ()
    resumed: tuple[dict, ...] = ()
    partial: dict | None = None
    deltas: tuple[dict, ...] = ()
    retried: tuple[str, ...] = ()
    # the run's record (cryptobench shared/results/run_record.py)
    run: dict = field(default_factory=dict)

    @property
    def display_units(self) -> DisplayUnits:
        return DisplayUnits.parse(self.units)

    def operations_of(self, engine_type: str) -> tuple[str, ...] | None:
        """Empty: the type falls back to TYPE_DEFAULT, whose invocation times nothing; None: not recorded."""
        if self.operations is None:
            return None
        return {t.upper(): ops for t, ops in self.operations.items()}.get(engine_type.upper(), ())

    def to_json(self) -> dict:
        optional = {"units": self.units, "energy": self.energy, "problems": list(self.problems),
                    "resumed": list(self.resumed), "partial": self.partial, "deltas": list(self.deltas), "retried": list(self.retried)}
        return {"schemaVersion": MANIFEST_DOC.version, "mode": self.mode, "config": self.config, "deviceId": self.deviceId,
                "inputs": self.inputs, **({"run": self.run} if self.run else {}), "runtime": self.runtime, "providers": [vars(p) for p in self.providers], "files": self.files,
                "counts": self.counts,
                **({"operations": {t: list(o) for t, o in self.operations.items()}} if self.operations is not None else {}),
                **{key: value for key, value in optional.items() if value}}

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
                   doc.get("inputs") or {}, _units(doc.get("units")), _operations(doc.get("operations")),
                   doc.get("energy"), tuple(doc.get("problems") or ()), tuple(doc.get("resumed") or ()), doc.get("partial"),
                   tuple(doc.get("deltas") or ()), tuple(doc.get("retried") or ()), doc.get("run") or {})
