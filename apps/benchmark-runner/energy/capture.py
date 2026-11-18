"""What a config node's harness.energy asks for: its capture and its source, else the default given."""

import pathlib

import yaml


def _defaults():
    """run.harness.energy of parity/defaults.yaml, which :config writes; found upward, since the two copies sit at different depths."""
    folder = next(f for f in pathlib.Path(__file__).resolve().parents if (f / "parity/defaults.yaml").is_file())
    return yaml.safe_load((folder / "parity/defaults.yaml").read_text())["run"]["harness"]["energy"]


DEFAULT = _defaults()


def _energy(node):
    return ((node or {}).get("harness") or {}).get("energy") or {}


def capture(node, default=DEFAULT["capture"]):
    return _energy(node).get("capture", default)


def source(node, default=DEFAULT["source"]):
    return _energy(node).get("source", default)
