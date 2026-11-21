"""Digests of what a run was given: providers.bundled, and global.yaml with its test set, bundled list and analysis left out."""
import copy, hashlib, json


from cryptobench.shared.settings import authored
from cryptobench.shared.errors.failures import CommandError
from cryptobench.shared.document.document import read_yaml


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def digests(global_file):
    """Parsed, not raw: a comment or a reordered key reruns nothing; the bundled list is its own input; analysis only
    shows results (charts, units), so changing it reruns no measurement."""
    given = authored.read(global_file)
    document = copy.deepcopy(given.document)
    document.pop("analysis", None)
    shipped = given.bundled
    (document.get("providers") or {}).pop("bundled", None)
    path = given.test_set
    if path and not path.is_file():
        raise CommandError(f"missing_file: {path} (selection.testSet)")
    selected = read_yaml(path) if path else None
    return {"bundled": digest(shipped), "config": digest({"global": document, "testSet": selected})}
