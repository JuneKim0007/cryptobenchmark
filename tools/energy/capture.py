"""Which energy capture a config node asks for: its harness.energy.capture, else the default given."""


def capture(node, default="none"):
    return (((node or {}).get("harness") or {}).get("energy") or {}).get("capture", default)
