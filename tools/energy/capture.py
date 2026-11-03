"""What a config node's harness.energy asks for: its capture and its source, else the default given."""


def _energy(node):
    return ((node or {}).get("harness") or {}).get("energy") or {}


def capture(node, default="none"):
    return _energy(node).get("capture", default)


def source(node, default="rails"):
    return _energy(node).get("source", default)
