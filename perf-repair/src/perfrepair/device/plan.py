"""Which device stages rerun and why: the current input digests against the manifest's and device.yaml's."""
from __future__ import annotations

from dataclasses import dataclass

from ..dto import BenchmarkManifest
from ..dto.device import DeviceRecord

STAGES = ("probe", "benchmark", "inbound", "screen")
LABELS = {"bundled": "providers.bundled", "config": "global.yaml", "names": "the names catalog",
          "screening": "the screening catalog"}
# a stage reruns when an input it reads changed, or a stage it reads from reruns
READS = {"probe": ("bundled", "config"), "benchmark": (), "inbound": (), "screen": ("names", "screening")}
AFTER = {"probe": (), "benchmark": ("probe",), "inbound": ("benchmark",), "screen": ("probe", "benchmark")}


@dataclass(frozen=True)
class Seen:
    """What the device folder holds now; record_problem says why record is None, inbound why its files are unusable."""
    manifest: BenchmarkManifest | None
    manifest_sha: str | None
    record: DeviceRecord | None
    record_problem: str | None
    inbound: str | None
    grouping: bool


def _changed(stage: str, recorded: dict, current: dict) -> str | None:
    changed = [LABELS[k] for k in READS[stage] if recorded.get(k) != current[k]]
    return f"{', '.join(changed)} changed" if changed else None


def _probe(seen: Seen, current: dict) -> str | None:
    if seen.manifest is None:
        return "no manifest.yaml"
    if not seen.manifest.inputs:
        return "the manifest records no inputs"
    return _changed("probe", seen.manifest.inputs, current)


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


CHECKS = {"probe": _probe, "benchmark": _benchmark, "inbound": _inbound, "screen": _screen}


def plan(seen: Seen, current: dict) -> dict[str, str | None]:
    """Per stage in order: None to reuse it, else the reason it runs."""
    out: dict[str, str | None] = {}
    for stage in STAGES:
        upstream = next((f"{before} reruns" for before in AFTER[stage] if out[before]), None)
        out[stage] = upstream or CHECKS[stage](seen, current)
    return out
