"""energy.json: joules per case from power-rail traces (measured: Jetpack's timed phase; dry: the case's marker)."""
import argparse, json, pathlib, sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from capture import capture  # noqa: E402
from rails import counters  # noqa: E402

MIN_POLLS = 20
# 2: source and kind
SCHEMA_VERSION = 2
SOURCE = "rails"
KIND = "measured"


class NotMeasured(Exception):
    pass


def window(rail_samples, start, end, idle_uj_per_ns, operations):
    if not rail_samples:
        raise NotMeasured("no_rails")
    try:
        per_rail = {name: counters.between(samples, start, end) for name, samples in rail_samples.items()}
    except counters.Uncovered:
        raise NotMeasured("window_uncovered") from None
    except counters.EmptyWindow:
        raise NotMeasured("empty_window") from None
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


def not_measured(reason, operations):
    """The case's record when it has no window to read; manafa's judge reads the same notMeasured."""
    return {"joules": None, "netJoules": None, "operations": operations, "joulesPerOperation": None,
            "windowSeconds": None, "polls": 0, "shortWindow": False, "rails": {}, "notMeasured": reason}


def judge(result, rails_responsive):
    reasons = [reason for reason, failed in (
        ("rails_unresponsive", not rails_responsive),
        (result.get("notMeasured"), "notMeasured" in result),
        ("no_operations", "notMeasured" not in result and not result["operations"]),
        ("short_window", result["shortWindow"]),
        ("net_not_positive", result["netJoules"] is not None and result["netJoules"] <= 0),
    ) if failed]
    if result["joulesPerOperation"] is None and not reasons:
        reasons.append("no_joules_per_operation")
    result.update(valid=not reasons, invalid=reasons)
    return result


def captures(prepared_path):
    prepared = yaml.safe_load(pathlib.Path(prepared_path).read_text()) or {}
    run = capture(prepared.get("run"))
    return {c["id"]: capture(c, run) for c in prepared.get("cases") or []}


def measured_cases(data_path, prepared_path, traces, idle, open_trace, measure=window):
    data = json.loads(pathlib.Path(data_path).read_text())
    wanted = {case for case, capture in captures(prepared_path).items() if capture == "measured"}
    out = {}
    for benchmark in data["benchmarks"]:
        name = benchmark["name"]
        case_id = name[name.index("[") + 1:-1] if "[" in name and name.endswith("]") else name
        if case_id in wanted:
            out[case_id] = measured_case(benchmark, traces, idle, open_trace, measure)
    return out


def measured_case(benchmark, traces, idle, open_trace, measure):
    operations = benchmark.get("repeatIterations", 0) * len(((benchmark.get("metrics") or {}).get("timeNs") or {}).get("runs") or [])
    trace_file = next((o["filename"] for o in benchmark.get("profilerOutputs") or [] if o.get("type") == "PerfettoTrace"), None)
    if trace_file is None or not (pathlib.Path(traces) / trace_file).is_file():
        return not_measured("trace_not_pulled", operations) | {"capture": "measured"}
    offset = None
    try:
        trace = open_trace(pathlib.Path(traces) / trace_file)
        try:
            start, end, offset = timed_window(trace)
            result = measure(trace.rails(), start, end, idle, operations)
        finally:
            trace.close()
    except NotMeasured as reason:
        result = not_measured(str(reason), operations)
    except Exception as error:  # a truncated trace fails inside trace_processor; that case alone has no energy
        result = not_measured(f"trace_unreadable: {one_line(error)}", operations)
    return result | {"capture": "measured", "clockOffsetNs": offset}


def timed_window(trace):
    phases = trace.timed_phases()
    if len(phases) != 1:
        raise NotMeasured(f"timed_phases: {len(phases)}")
    offset = trace.boot_minus_monotonic()
    if offset is None:
        raise NotMeasured("no_clock_snapshot")
    start, end = (ts + offset for ts in phases[0])
    return start, end, offset


def one_line(error):
    return " ".join(str(error).split())[:200] or type(error).__name__


def dry_cases(trace_path, calls_path, idle, open_trace, measure=window):
    calls = yaml.safe_load(pathlib.Path(calls_path).read_text()) or {}
    trace = open_trace(trace_path)
    try:
        markers, rail_samples = trace.markers(), trace.rails()
    finally:
        trace.close()
    out = {}
    for case_id, (start, end) in sorted(markers.items()):
        try:
            if case_id not in calls:
                raise NotMeasured("no_call_count")
            result = measure(rail_samples, start, end, idle, calls[case_id])
        except NotMeasured as reason:
            result = not_measured(str(reason), calls.get(case_id))
        # Markers and rails are both atrace/BOOTTIME in one session: no second clock to disagree with.
        out[case_id] = result | {"capture": "dry", "clockOffsetNs": 0}
    return out


def parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--capability", required=True)
    ap.add_argument("--prepared")
    ap.add_argument("--benchmark-data")
    ap.add_argument("--traces")
    ap.add_argument("--dry-trace")
    ap.add_argument("--dry-calls")
    ap.add_argument("-o", "--out", required=True)
    return ap


def read_cases(a, idle, open_trace, measure=window):
    cases = {}
    if a.benchmark_data:
        cases.update(measured_cases(a.benchmark_data, a.prepared, a.traces, idle, open_trace, measure))
    if a.dry_trace:
        cases.update(dry_cases(a.dry_trace, a.dry_calls, idle, open_trace, measure))
    return cases


def report_cases(cases):
    invalid = {c: r["invalid"] for c, r in cases.items() if not r["valid"]}
    print(f"energy:    {len(cases)} cases, {len(cases) - len(invalid)} valid")
    for c, reasons in invalid.items():
        print(f"invalid:   {c}: {', '.join(reasons)}")


def main(argv=None):
    a = parser().parse_args(argv)
    from rails.trace import Trace

    capability = yaml.safe_load(pathlib.Path(a.capability).read_text())
    idle = capability["idleMicrojoules"] / (capability["windowSeconds"] * 1e9)
    cases = {c: judge(r, capability["railsResponsive"]) for c, r in read_cases(a, idle, Trace).items()}
    document = {"schemaVersion": SCHEMA_VERSION, "source": SOURCE, "kind": KIND, "railsResponsive": capability["railsResponsive"], "cases": cases}
    pathlib.Path(a.out).write_text(json.dumps(document, indent=1))
    report_cases(cases)
    return 0


if __name__ == "__main__":
    sys.exit(main())
