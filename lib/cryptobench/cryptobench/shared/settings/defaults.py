"""contracts/defaults/defaults.yaml: the value :config writes for each key a config leaves out (DefaultsDocument.kt writes the file)."""
import functools

from cryptobench.shared import paths
from cryptobench.shared.document.document import read_yaml


@functools.cache
def _document():
    return read_yaml(paths.repo().defaults)


def at(path):
    """The default at a dotted path, or None where :config has none (orderSeed, thermalGate, a harness key)."""
    value = _document()
    for key in path.split("."):
        value = value.get(key) if isinstance(value, dict) else None
    return value
