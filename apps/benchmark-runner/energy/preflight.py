"""usage: preflight.py <idle.pftrace> <busy.pftrace> <idle seconds> <busy seconds> <out energy.yaml> [--accept-unresponsive] [--skin <json>]
       preflight.py --end <idle.pftrace> <idle seconds> <energy.yaml> [--skin <json>]: the run's end idle reading, added to energy.yaml
--skin: {"start": {"sensor", "celsius"} | null, "end": ...}, the skin temperature at the idle reading's start and end"""
import json, pathlib, sys

import yaml

from energy import CAPABILITY_VERSION  # noqa: E402
from rails import counters  # noqa: E402

RESPONSIVE = 1.10  # a busy window must draw at least 10% more power than an idle one
SKIN = "--skin"


def reading(rails):
    """A window's microjoules over the summed rails, the BOOTTIME midpoint of their samples (None without samples) and their span in seconds."""
    times = [t for samples in rails.summed.values() for t, _ in samples]
    if not times:
        return 0, None, 0.0
    return sum(counters.whole(s) for s in rails.summed.values()), (min(times) + max(times)) // 2, (max(times) - min(times)) / 1e9


def excluded(rails):
    return sum(counters.whole(s) for s in rails.excluded.values())


def subsystems_text(rails):
    def names(group):
        return ", ".join(sorted({str(rails.subsystems.get(raw)) for raw in group})) or "none"
    return f"summed subsystems {names(rails.summed)} vs excluded {names(rails.excluded)}"


def microwatts(microjoules, span):
    """Power over the span the samples cover, not the configured length: a short or cut trace keeps its true rate."""
    return microjoules / span if span > 0 else 0.0


def capability(idle_rails, busy_rails, idle_seconds, busy_seconds, accept, skin=None):
    idle, idle_at, idle_span = reading(idle_rails)
    busy, _, busy_span = reading(busy_rails)
    present = bool(idle_rails.summed) and bool(busy_rails.summed)
    return {"schemaVersion": CAPABILITY_VERSION, "railsPresent": present,
            "railsResponsive": present and idle > 0 and microwatts(busy, busy_span) >= microwatts(idle, idle_span) * RESPONSIVE,
            "idleMicrojoules": idle, "busyMicrojoules": busy, "idleExcludedMicrojoules": excluded(idle_rails),
            "busyExcludedMicrojoules": excluded(busy_rails), "idleWindowSeconds": idle_seconds, "busyWindowSeconds": busy_seconds,
            "idleSpanSeconds": idle_span, "idleMicrowatts": microwatts(idle, idle_span), "idleBoottimeNs": idle_at,
            "idleSkin": skin, "acceptUnresponsive": accept, "railSubsystems": dict(sorted(busy_rails.subsystems.items()))}


def ended(document, end_rails, seconds, skin=None):
    idle, at, span = reading(end_rails)
    if at is None:
        raise SystemExit("no_rails: the end idle trace has no summed power rails")
    start, end = document["idleMicrowatts"], microwatts(idle, span)
    drift = (end - start) / start * 100 if start else None
    return document | {"idleEndMicrojoules": idle, "idleEndExcludedMicrojoules": excluded(end_rails), "idleEndWindowSeconds": seconds,
                       "idleEndSpanSeconds": span, "idleEndMicrowatts": end, "idleEndBoottimeNs": at, "idleEndSkin": skin, "idleDriftPercent": drift}


def rails_of(path):
    from rails.trace import Trace
    trace = Trace(path)
    try:
        return trace.rails()
    finally:
        trace.close()


def skin_text(skin):
    def one(stamp):
        return f"{stamp['celsius']:.1f} C" if stamp else "unread"
    if not skin:
        return "skin unread"
    sensors = sorted({stamp["sensor"] for stamp in skin.values() if stamp})
    return f"skin {one(skin.get('start'))} -> {one(skin.get('end'))}" + (f" ({', '.join(sensors)})" if sensors else "")


def end(trace_path, seconds, out, skin=None):
    document = ended(yaml.safe_load(pathlib.Path(out).read_text()), rails_of(trace_path), float(seconds), skin)
    pathlib.Path(out).write_text(yaml.safe_dump(document, sort_keys=False))
    hours = (document["idleEndBoottimeNs"] - (document["idleBoottimeNs"] or 0)) / 3.6e12
    drift = "n/a" if document["idleDriftPercent"] is None else f"{document['idleDriftPercent']:+.1f}%"
    print(f"idle:      start {document['idleMicrowatts'] / 1e6:.4f} W, end {document['idleEndMicrowatts'] / 1e6:.4f} W, {hours:.2f} h apart, "
          f"drift {drift}; end {document['idleEndSpanSeconds']:.1f} of {document['idleEndWindowSeconds']} s, {skin_text(skin)}")


def split(argv):
    """The positional arguments, the flags without a value, and --skin's JSON."""
    skin = json.loads(argv[argv.index(SKIN) + 1]) if SKIN in argv else None
    rest = [a for i, a in enumerate(argv) if a != SKIN and (i == 0 or argv[i - 1] != SKIN)]
    return [a for a in rest if not a.startswith("--")], {a for a in rest if a.startswith("--")}, skin


def main(argv=None):
    positional, flags, skin = split(sys.argv[1:] if argv is None else argv)
    if "--end" in flags:
        end(*positional, skin=skin)
        return 0
    idle_path, busy_path, idle_seconds, busy_seconds, out = positional
    busy = rails_of(busy_path)
    document = capability(rails_of(idle_path), busy, float(idle_seconds), float(busy_seconds), "--accept-unresponsive" in flags, skin)
    pathlib.Path(out).write_text(yaml.safe_dump(document, sort_keys=False))
    print(f"rails:     present {document['railsPresent']}, responsive {document['railsResponsive']} "
          f"(idle {document['idleMicrojoules']:.0f} uJ over {document['idleSpanSeconds']:.1f} of {idle_seconds} s, {skin_text(skin)}; "
          f"busy {document['busyMicrojoules']:.0f} uJ over {busy_seconds} s; "
          f"excluded idle {document['idleExcludedMicrojoules']:.0f} uJ, busy {document['busyExcludedMicrojoules']:.0f} uJ; {subsystems_text(busy)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
