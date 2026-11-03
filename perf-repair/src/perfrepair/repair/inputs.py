"""A scope's harness inputs: the app's static sizes when the scope has any, else the run's configured sizes."""
from __future__ import annotations

from pathlib import Path

from ..data_handler.inbound.manifest import manifest_file, read_manifest
from ..dto.grouping import parse_qualified
from ..dto.site import Scope
from ..files import read_yaml
from ..stop.halt import Coded


def read_effective(manifest: Path) -> dict:
    found, base = read_manifest(manifest)
    path = manifest_file(found, base, "effective")
    if path is None:
        raise Coded(f"missing_effective: {manifest} lists no files.effective; the run's sizes are unknown")
    return read_yaml(path)


def _entries(effective: dict, item: str) -> list[dict]:
    """Every `name` and `name@group` entry of the item; names match case-insensitively, as JCA names do."""
    engine_type, name, provider = parse_qualified(item)
    by_name = effective["providers"].get(provider, {}).get(engine_type, {})
    entries = [e or {} for key, e in by_name.items() if key.split("@")[0].lower() == name.lower()]
    if not entries:
        raise Coded(f"item_not_configured: {item} has no providers.{provider}.{engine_type}.{name} entry "
                         f"in effective.yaml; the results are not the run the groups were built from")
    return entries


def configured(effective: dict, item: str) -> tuple[set[int], set[int]]:
    """Input and key sizes the run measured the item at; an entry without inputSizes takes run.inputSizes."""
    entries = _entries(effective, item)
    return ({size for e in entries for size in e.get("inputSizes") or effective["run"]["inputSizes"]},
            {size for e in entries for size in e.get("keySizes") or ()})


def scope_inputs(scope: Scope, current: str, option: str, effective: dict) -> dict:
    """Run sizes: the largest one configured for both items, so before and after run at a measured size."""
    if scope.inputSize is not None or scope.keySize is not None:
        return {"inputSize": scope.inputSize, "keySize": scope.keySize, "from": "app"}
    (inputs_a, keys_a), (inputs_b, keys_b) = configured(effective, current), configured(effective, option)
    return {"inputSize": max(inputs_a & inputs_b, default=None), "keySize": max(keys_a & keys_b, default=None),
            "from": "run"}
