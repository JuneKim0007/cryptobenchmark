"""energy.json: joules per case from power-rail traces (measured: Jetpack's timed phase; dry: the case's marker)."""
import argparse, json, pathlib, sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from capture import capture  # noqa: E402
from rails import counters  # noqa: E402

MIN_POLLS = 20


def window(rail_samples, start, end, idle_uj_per_ns, operations):
    per_rail = {name: counters.between(samples, start, end) for name, samples in rail_samples.items()}
    gross_uj = sum(per_rail.values())
    net_uj = gross_uj - idle_uj_per_ns * (end - start)
    polls = min(counters.polls_inside(s, start, end) for s in rail_samples.values())
    return {
        "joules": gross_uj / 1e6,
        "netJoules": net_uj / 1e6,
        "operations": operations,
        "joulesPerOperation": net_uj / 1e6 / operations if operations else None,
        "windowSeconds": (end - start) / 1e9,
        "polls": polls,
        "shortWindow": polls < MIN_POLLS,
        "rails": {name: uj / 1e6 for name, uj in sorted(per_rail.items())},
    }


def judge(result, rails_responsive):
    reasons = [reason for reason, failed in (
        ("rails_unresponsive", not rails_responsive),
        ("short_window", result["shortWindow"]),
        ("net_not_positive", result["netJoules"] <= 0),
    ) if failed]
    result.update(valid=not reasons, invalid=reasons)
    return result


def captures(prepared_path):
    prepared = yaml.safe_load(pathlib.Path(prepared_path).read_text()) or {}
    run = capture(prepared.get("run"))
    return {c["id"]: capture(c, run) for c in prepared.get("cases") or []}


def measured_cases(data_path, prepared_path, traces, idle, open_trace):
    data = json.loads(pathlib.Path(data_path).read_text())
    wanted = {case for case, capture in captures(prepared_path).items() if capture == "measured"}
    out = {}
    for benchmark in data["benchmarks"]:
        name = benchmark["name"]
        case_id = name[name.index("[") + 1:-1] if "[" in name else name
        if case_id not in wanted:
            continue
        trace_file = next((o["filename"] for o in benchmark.get("profilerOutputs") or [] if o["type"] == "PerfettoTrace"), None)
        if trace_file is None or not (pathlib.Path(traces) / trace_file).is_file():
            raise ValueError(f"{case_id}: measured energy, but its Jetpack trace {trace_file} was not pulled into {traces}")
        trace = open_trace(pathlib.Path(traces) / trace_file)
        try:
            phases = trace.timed_phases()
            if len(phases) != 1:
                raise ValueError(f"{case_id}: {len(phases)} timed phases in {trace_file}")
            offset = trace.boot_minus_monotonic()
            if offset is None:
                raise ValueError(f"{case_id}: {trace_file} has no BOOTTIME/MONOTONIC snapshot to place its phase on the rails' clock")
            start, end = (ts + offset for ts in phases[0])
            runs = len(benchmark["metrics"]["timeNs"]["runs"])
            result = window(trace.rails(), start, end, idle, benchmark["repeatIterations"] * runs)
            result.update(capture="measured", clockOffsetNs=offset)
            out[case_id] = result
        finally:
            trace.close()
    return out


def dry_cases(trace_path, calls_path, idle, open_trace):
    calls = yaml.safe_load(pathlib.Path(calls_path).read_text()) or {}
    trace = open_trace(trace_path)
    try:
        markers, rail_samples = trace.markers(), trace.rails()
    finally:
        trace.close()
    out = {}
    for case_id, (start, end) in sorted(markers.items()):
        if case_id not in calls:
            raise ValueError(f"{case_id}: a marker without a call count in {calls_path}")
        result = window(rail_samples, start, end, idle, calls[case_id])
        # Markers and rails are both atrace/BOOTTIME in one session: no second clock to disagree with.
        result.update(capture="dry", clockOffsetNs=0)
        out[case_id] = result
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--capability", required=True)
    ap.add_argument("--prepared")
    ap.add_argument("--benchmark-data")
    ap.add_argument("--traces")
    ap.add_argument("--dry-trace")
    ap.add_argument("--dry-calls")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args(argv)
    from rails.trace import Trace

    capability = yaml.safe_load(pathlib.Path(a.capability).read_text())
    idle = capability["idleMicrojoules"] / (capability["windowSeconds"] * 1e9)
    cases = {}
    if a.benchmark_data:
        cases.update(measured_cases(a.benchmark_data, a.prepared, a.traces, idle, Trace))
    if a.dry_trace:
        cases.update(dry_cases(a.dry_trace, a.dry_calls, idle, Trace))
    cases = {c: judge(r, capability["railsResponsive"]) for c, r in cases.items()}
    document = {"schemaVersion": 1, "railsResponsive": capability["railsResponsive"], "cases": cases}
    pathlib.Path(a.out).write_text(json.dumps(document, indent=1))
    invalid = {c: r["invalid"] for c, r in cases.items() if not r["valid"]}
    print(f"energy:    {len(cases)} cases, {len(cases) - len(invalid)} valid")
    for c, reasons in invalid.items():
        print(f"invalid:   {c}: {', '.join(reasons)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
