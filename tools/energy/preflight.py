"""usage: preflight.py <idle.pftrace> <busy.pftrace> <window seconds> <out energy.yaml> [--accept-unresponsive]"""
import pathlib, sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rails import counters  # noqa: E402

RESPONSIVE = 1.10  # a busy window must use at least 10% more energy than an idle one


def capability(idle_rails, busy_rails, seconds, accept):
    idle = sum(counters.whole(s) for s in idle_rails.values())
    busy = sum(counters.whole(s) for s in busy_rails.values())
    present = bool(idle_rails) and bool(busy_rails)
    return {"schemaVersion": 1, "railsPresent": present,
            "railsResponsive": present and idle > 0 and busy >= idle * RESPONSIVE,
            "idleMicrojoules": idle, "busyMicrojoules": busy, "windowSeconds": seconds,
            "acceptUnresponsive": accept}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    accept = "--accept-unresponsive" in argv
    idle_path, busy_path, seconds, out = [a for a in argv if a != "--accept-unresponsive"]
    from rails.trace import Trace
    readings = []
    for path in (idle_path, busy_path):
        trace = Trace(path)
        try:
            readings.append(trace.rails())
        finally:
            trace.close()
    document = capability(readings[0], readings[1], float(seconds), accept)
    pathlib.Path(out).write_text(yaml.safe_dump(document, sort_keys=False))
    print(f"rails:     present {document['railsPresent']}, responsive {document['railsResponsive']} "
          f"(idle {document['idleMicrojoules']:.0f} uJ, busy {document['busyMicrojoules']:.0f} uJ over {seconds} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
