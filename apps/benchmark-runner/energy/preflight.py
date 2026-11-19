"""usage: preflight.py <idle.pftrace> <busy.pftrace> <idle seconds> <busy seconds> <out energy.yaml> [--accept-unresponsive]"""
import pathlib, sys

import yaml

from energy import CAPABILITY_VERSION  # noqa: E402
from rails import counters  # noqa: E402

RESPONSIVE = 1.10  # a busy window must draw at least 10% more power than an idle one


def capability(idle_rails, busy_rails, idle_seconds, busy_seconds, accept):
    idle = sum(counters.whole(s) for s in idle_rails.values())
    busy = sum(counters.whole(s) for s in busy_rails.values())
    present = bool(idle_rails) and bool(busy_rails)
    return {"schemaVersion": CAPABILITY_VERSION, "railsPresent": present,
            "railsResponsive": present and idle > 0 and busy / busy_seconds >= idle / idle_seconds * RESPONSIVE,
            "idleMicrojoules": idle, "busyMicrojoules": busy, "idleWindowSeconds": idle_seconds, "busyWindowSeconds": busy_seconds,
            "acceptUnresponsive": accept}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    accept = "--accept-unresponsive" in argv
    idle_path, busy_path, idle_seconds, busy_seconds, out = [a for a in argv if a != "--accept-unresponsive"]
    from rails.trace import Trace
    readings = []
    for path in (idle_path, busy_path):
        trace = Trace(path)
        try:
            readings.append(trace.rails())
        finally:
            trace.close()
    document = capability(readings[0], readings[1], float(idle_seconds), float(busy_seconds), accept)
    pathlib.Path(out).write_text(yaml.safe_dump(document, sort_keys=False))
    print(f"rails:     present {document['railsPresent']}, responsive {document['railsResponsive']} "
          f"(idle {document['idleMicrojoules']:.0f} uJ over {idle_seconds} s, busy {document['busyMicrojoules']:.0f} uJ over {busy_seconds} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
