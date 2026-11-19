"""usage: preflight.py <idle.pftrace> <busy.pftrace> <idle seconds> <busy seconds> <out energy.yaml> [--accept-unresponsive]
       preflight.py --end <idle.pftrace> <idle seconds> <energy.yaml>: the run's end idle reading, added to energy.yaml"""
import pathlib, sys

import yaml

from energy import CAPABILITY_VERSION  # noqa: E402
from rails import counters  # noqa: E402

RESPONSIVE = 1.10  # a busy window must draw at least 10% more power than an idle one


def reading(rails):
    """A window's microjoules over every rail and the BOOTTIME midpoint of its samples (None without samples)."""
    times = [t for samples in rails.values() for t, _ in samples]
    return sum(counters.whole(s) for s in rails.values()), (min(times) + max(times)) // 2 if times else None


def capability(idle_rails, busy_rails, idle_seconds, busy_seconds, accept):
    idle, idle_at = reading(idle_rails)
    busy, _ = reading(busy_rails)
    present = bool(idle_rails) and bool(busy_rails)
    return {"schemaVersion": CAPABILITY_VERSION, "railsPresent": present,
            "railsResponsive": present and idle > 0 and busy / busy_seconds >= idle / idle_seconds * RESPONSIVE,
            "idleMicrojoules": idle, "busyMicrojoules": busy, "idleWindowSeconds": idle_seconds, "busyWindowSeconds": busy_seconds,
            "idleBoottimeNs": idle_at, "acceptUnresponsive": accept}


def ended(document, end_rails, seconds):
    idle, at = reading(end_rails)
    if at is None:
        raise SystemExit("no_rails: the end idle trace has no power rails")
    start = document["idleMicrojoules"] / document["idleWindowSeconds"]
    drift = (idle / seconds - start) / start * 100 if start else None
    return document | {"idleEndMicrojoules": idle, "idleEndWindowSeconds": seconds, "idleEndBoottimeNs": at, "idleDriftPercent": drift}


def rails_of(path):
    from rails.trace import Trace
    trace = Trace(path)
    try:
        return trace.rails()
    finally:
        trace.close()


def end(trace_path, seconds, out):
    document = ended(yaml.safe_load(pathlib.Path(out).read_text()), rails_of(trace_path), float(seconds))
    pathlib.Path(out).write_text(yaml.safe_dump(document, sort_keys=False))
    start_watts = document["idleMicrojoules"] / document["idleWindowSeconds"] / 1e6
    end_watts = document["idleEndMicrojoules"] / document["idleEndWindowSeconds"] / 1e6
    hours = (document["idleEndBoottimeNs"] - (document["idleBoottimeNs"] or 0)) / 3.6e12
    drift = "n/a" if document["idleDriftPercent"] is None else f"{document['idleDriftPercent']:+.1f}%"
    print(f"idle:      start {start_watts:.4f} W, end {end_watts:.4f} W, {hours:.2f} h apart, drift {drift}")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--end"]:
        end(*argv[1:])
        return 0
    accept = "--accept-unresponsive" in argv
    idle_path, busy_path, idle_seconds, busy_seconds, out = [a for a in argv if a != "--accept-unresponsive"]
    document = capability(rails_of(idle_path), rails_of(busy_path), float(idle_seconds), float(busy_seconds), accept)
    pathlib.Path(out).write_text(yaml.safe_dump(document, sort_keys=False))
    print(f"rails:     present {document['railsPresent']}, responsive {document['railsResponsive']} "
          f"(idle {document['idleMicrojoules']:.0f} uJ over {idle_seconds} s, busy {document['busyMicrojoules']:.0f} uJ over {busy_seconds} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
