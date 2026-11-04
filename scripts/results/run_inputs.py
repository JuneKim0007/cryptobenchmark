"""Digests of what a run was given: providers.bundled, and global.yaml with its test set, bundled list and analysis left out."""
import copy, hashlib, json

import yaml

import bundled


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def digests(global_file):
    """Parsed, not raw: a comment or a reordered key reruns nothing; the bundled list is its own input; analysis only
    shows results (charts, units), so changing it reruns no measurement."""
    document = copy.deepcopy(yaml.safe_load(global_file.read_text()) or {})
    document.pop("analysis", None)
    shipped = bundled.read(global_file)
    (document.get("providers") or {}).pop("bundled", None)
    test_set = (document.get("selection") or {}).get("testSet")
    path = global_file.parent / test_set if test_set else None
    selected = yaml.safe_load(path.read_text()) if path and path.is_file() else None
    return {"bundled": digest(shipped), "config": digest({"global": document, "testSet": selected})}
