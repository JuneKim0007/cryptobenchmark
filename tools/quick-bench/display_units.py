"""analysis.units: time and throughput in the units a reader chose; statistics stay on ns/op, MB is 10^6 bytes."""

NS_PER = {"ms": 1e6, "us": 1e3, "ns": 1.0}
# bytes per unit; ops/s counts calls, so it needs no input size
BYTES_PER = {"MB/s": 1e6, "MiB/s": 2 ** 20, "ops/s": None}


def check(units):
    if units["latency"] not in NS_PER or units["throughput"] not in BYTES_PER:
        raise ValueError(f"invalid: analysis.units {units}, latency one of {list(NS_PER)}, throughput one of {list(BYTES_PER)}")
    return units


def latency_label(units):
    return f"{units['latency']}/op"


def latency(ns, units):
    return ns / NS_PER[units["latency"]]


def throughput(ns, size, units):
    """None where the unit needs an input size the case does not have, or the time is zero."""
    per = BYTES_PER[units["throughput"]]
    if not ns or (per is not None and not size):
        return None
    return 1e9 / ns * (1 if per is None else size / per)


def number(value):
    """Significant figures, so a sub-unit value never rounds to 0; thousands grouped above 1000."""
    return "-" if value is None else f"{value:,.0f}" if abs(value) >= 1000 else f"{value:.4g}"
