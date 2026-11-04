"""The setup a benchmark measured under, read from its own folder, and the first field two setups differ in: a delta is
merged only into a benchmark of the same setup."""
from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..data_handler.inbound import read_manifest
from ..data_handler.inbound.manifest import manifest_file
from ..files import read_yaml

# device id carries the build fingerprint; the runtime fields that change what one call costs
RUNTIME = ("fingerprint", "compilationMode", "sdkInt", "javaRuntimeVersion")
# the run block minus selection: everything a case's numbers depend on
CASE_FIELDS = ("resolvedParameters", "harness", "metrics", "perCall")


def _flat(prefix: str, value, out: dict) -> dict:
    if isinstance(value, dict):
        for k in sorted(value):
            _flat(f"{prefix}.{k}" if prefix else k, value[k], out)
    else:
        out[prefix] = value
    return out


def _bundled(manifest, base: Path) -> list[str]:
    probe = manifest_file(manifest, base, "probe")
    providers = (read_yaml(probe).get("providers") or []) if probe else []
    return sorted(f"{p['name']}={p.get('artifact')}@{p.get('version')}" for p in providers if p.get("origin") == "bundled")


def fingerprint(folder: Path) -> dict:
    """Flat `field: value` pairs; a field one folder lacks reads None."""
    manifest, base = read_manifest(Path(folder) / rd.MANIFEST)
    effective = manifest_file(manifest, base, "effective")
    prepared = manifest_file(manifest, base, "prepared")
    run = (read_yaml(effective).get("run") or {}) if effective else {}
    planned = (read_yaml(prepared).get("run") or {}) if prepared else {}
    out = {"deviceId": manifest.deviceId, "mode": manifest.mode, "bundled": _bundled(manifest, base),
           "processes": len(manifest.files.get("processes") or ())}
    out.update({f"runtime.{k}": manifest.runtime.get(k) for k in RUNTIME})
    return _flat("prepared", planned, _flat("run", run, out))


def case_setups(folder: Path) -> dict[str, dict]:
    """Per planned case, what the test set's overrides set on it; an anchor must have been planned alike."""
    manifest, base = read_manifest(Path(folder) / rd.MANIFEST)
    prepared = manifest_file(manifest, base, "prepared")
    cases = (read_yaml(prepared).get("cases") or []) if prepared else []
    return {c["id"]: {k: c.get(k) for k in CASE_FIELDS} for c in cases}


def differing(stored: dict, now: dict) -> list[str]:
    """`<field>: <stored> stored, <now> now` per field that differs, in field order."""
    return [f"{k}: {stored.get(k)!r} stored, {now.get(k)!r} now" for k in sorted(set(stored) | set(now))
            if stored.get(k) != now.get(k)]
