"""device.yaml: what the device stage last finished with; its digests, not the device id, decide a rerun."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from cryptobench.catalogue.document import DocumentKind

SCHEMA_VERSION = 1
DEVICE_DOC = DocumentKind("device.yaml", SCHEMA_VERSION)
INPUTS = ("bundled", "config", "names", "screening")
RUNTIME_KEYS = ("model", "manufacturer", "sdkInt", "release", "osName", "osArch", "javaVersion", "javaVendor",
                "javaRuntimeVersion")


@dataclass(frozen=True)
class DeviceRecord:
    deviceId: str
    mode: str
    runtime: dict
    inputs: dict[str, str]
    manifest: str
    # the digests primitives.tsv was made from; a record without them reruns only that stage
    primitives: dict[str, str | None] = field(default_factory=dict)
    # with device.filterByApps: the generated config's digest, the measured set's digest and its items; empty = the base
    benchmark: dict = field(default_factory=dict)
    # with device.bundled.fromApps apply: the applied entries' digest and the bundled digest the manifest then records
    bundled: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        return {"schemaVersion": SCHEMA_VERSION, **asdict(self)}

    @classmethod
    def from_json(cls, doc: dict) -> "DeviceRecord":
        DEVICE_DOC.check(doc)
        missing = sorted(set(INPUTS) - set(doc.get("inputs") or {}))
        if missing or not doc.get("manifest"):
            raise ValueError(f"device.yaml lacks {', '.join(missing) or 'manifest'}")
        return cls(str(doc["deviceId"]), str(doc["mode"]), doc.get("runtime") or {}, dict(doc["inputs"]), doc["manifest"],
                   dict(doc.get("primitives") or {}), dict(doc.get("benchmark") or {}),
                   dict(doc.get("bundled") or {}))


def runtime_summary(runtime: dict) -> dict:
    return {k: runtime[k] for k in RUNTIME_KEYS if runtime.get(k) not in (None, "")}
