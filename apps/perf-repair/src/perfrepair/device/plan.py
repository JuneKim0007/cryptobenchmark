"""Which device stages rerun and why: the current input digests against the manifest's and device.yaml's."""
from __future__ import annotations

from dataclasses import dataclass

from ..dto import BenchmarkManifest
from ..dto.device import DeviceRecord

STAGES = ("probe", "benchmark", "inbound", "screen", "primitives")
LABELS = {"bundled": "providers.bundled", "config": "global.yaml", "names": "the names catalog",
          "screening": "the screening catalog", "rows": "rows.json", "measurements": "measurements.json",
          "screen": "grouping/screen.json"}
# a stage reruns when an input it reads changed, or a stage it reads from reruns
READS = {"probe": ("bundled", "config"), "benchmark": (), "inbound": (), "screen": ("names", "screening"),
         "primitives": ("rows", "measurements", "screen")}
AFTER = {"probe": (), "benchmark": ("probe",), "inbound": ("benchmark",), "screen": ("probe", "benchmark"),
         "primitives": ("inbound", "screen")}
REFRESH = "--refresh"


@dataclass(frozen=True)
class Seen:
    """What the device folder holds now; record_problem says why record is None, inbound why its files are unusable."""
    manifest: BenchmarkManifest | None
    manifest_sha: str | None
    record: DeviceRecord | None
    record_problem: str | None
    inbound: str | None
    grouping: bool
    # why primitives.tsv is rebuilt whatever its inputs; None when it is there in this schema
    primitives: str | None
    # the digests primitives.tsv would be made from now
    made_from: dict[str, str | None]

    @property
    def scoped(self) -> dict:
        return (self.record.benchmark or self.record.bundled) if self.record else {}

    @property
    def kept(self) -> dict:
        return self.record.benchmark if self.record else {}

    @property
    def applied(self) -> str | None:
        return self.record.bundled.get("applied") if self.record else None


def _changed(stage: str, recorded: dict, current: dict) -> str | None:
    changed = [LABELS[k] for k in READS[stage] if recorded.get(k) != current[k]]
    return f"{', '.join(changed)} changed" if changed else None


def mapped_inputs(inputs: dict, record: DeviceRecord | None) -> dict:
    """A used-set or applied-bundled benchmark's manifest carries its generated config's digests; device.yaml maps them
    back to the base's."""
    inputs = dict(inputs)
    if record is None:
        return inputs
    generated = {"config": {record.benchmark.get("config"), record.bundled.get("config")},
                 "bundled": {record.bundled.get("bundled")}}
    for key, digests in generated.items():
        if inputs.get(key) in digests - {None}:
            inputs[key] = record.inputs[key]
    return inputs


def base_inputs(seen: Seen) -> dict:
    return mapped_inputs(seen.manifest.inputs, seen.record)


def _probe(seen: Seen, current: dict) -> str | None:
    if seen.manifest is None:
        return "no manifest.yaml"
    if not seen.manifest.inputs:
        return "the manifest records no inputs"
    return _changed("probe", base_inputs(seen), current)


def _benchmark(seen: Seen, current: dict) -> str | None:
    return None if "benchmark" in seen.manifest.files else "the manifest lists no benchmark"


def _record(seen: Seen) -> str | None:
    if seen.record is None:
        return seen.record_problem
    return None if seen.record.manifest == seen.manifest_sha else "manifest.yaml is not the one device.yaml recorded"


def _inbound(seen: Seen, current: dict) -> str | None:
    return seen.inbound or _record(seen)


def _screen(seen: Seen, current: dict) -> str | None:
    if not seen.grouping:
        return "grouping/screen.json missing"
    return _record(seen) or _changed("screen", seen.record.inputs, current)


def _primitives(seen: Seen, current: dict) -> str | None:
    if seen.primitives:
        return seen.primitives
    if problem := _record(seen):
        return problem
    if not seen.record.primitives:
        return "device.yaml records no primitives.tsv inputs"
    return _changed("primitives", seen.record.primitives, seen.made_from)


CHECKS = {"probe": _probe, "benchmark": _benchmark, "inbound": _inbound, "screen": _screen, "primitives": _primitives}


def plan(seen: Seen, current: dict, refresh: bool = False, forced: dict[str, str] | None = None) -> dict[str, str | None]:
    """Per stage in order: None to reuse it, else the reason it runs; refresh reruns the static table, never a device run;
    forced: a reason a stage reruns that no digest holds (the used set)."""
    out: dict[str, str | None] = {}
    for stage in STAGES:
        upstream = next((f"{before} reruns" for before in AFTER[stage] if out[before]), None)
        out[stage] = upstream or (forced or {}).get(stage) or CHECKS[stage](seen, current)
    if refresh and not out["primitives"]:
        out["primitives"] = REFRESH
    return out
