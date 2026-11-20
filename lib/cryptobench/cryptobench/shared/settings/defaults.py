"""defaults.yaml beside this file: the value :config writes for each key a config leaves out (DefaultsDocument.kt writes the file)."""
import functools
from importlib import resources

from cryptobench.shared.document.document import parse_yaml


@functools.cache
def _document():
    return parse_yaml(resources.files(__package__).joinpath("defaults.yaml").read_text(encoding="utf-8"), "defaults.yaml")


def at(path):
    """The default at a dotted path, or None where :config has none (orderSeed, thermalGate.temperatureKeptCelsius, most harness keys)."""
    value = _document()
    for key in path.split("."):
        value = value.get(key) if isinstance(value, dict) else None
    return value
