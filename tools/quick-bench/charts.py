"""IQR bar charts, one per chart group, operation and fixed input size, plus the summary and the data they plot.

    charts.py <benchmark.json> <prepared.yaml> <effective.yaml> <results>

Reads what the run already wrote and draws only what analysis.charts in effective.yaml names (default: all, of
which this file draws iqrBars; analyze.py draws throughput, latency and stability from the same list). Statistics are taken on the measured ns/op,
then shown as MB/s or us/op.

    chart_input   what is read           chart_model   one case, summarised     chart_draw    matplotlib only
    chart_report  summary, data, manifest
"""
import pathlib
import sys
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import chart_draw  # noqa: E402
import chart_input  # noqa: E402
import chart_model  # noqa: E402
import chart_report  # noqa: E402


def build(benchmark_file, prepared_file, effective_file, results):
    raw, groups, effective = chart_input.load(benchmark_file, prepared_file, effective_file)
    cfg = chart_input.settings(effective)
    cases = [chart_model.summarize_case(c, groups, cfg) for c in raw]
    ungrouped = sum(1 for c in cases if c["group"] == chart_input.UNIDENTIFIED[0])
    if ungrouped:
        print(f"warning: {ungrouped} of {len(cases)} cases have no chartGroup in {prepared_file}; they are drawn as group 0. "
              "Run preparation again: groups come from the service type, not from this script.", file=sys.stderr)
    mismatches = chart_report.audit_summary(cases)["mismatches"]
    if mismatches:
        print(f"warning: {len(mismatches)} cases disagree with the statistics androidx reported for the same runs "
              f"(first: {mismatches[0]}); see auditAgainstJetpack in manifest.yaml", file=sys.stderr)
    root = pathlib.Path(cfg["dir"].replace("<run-id>", cfg["run_id"])) if cfg["dir"] else pathlib.Path(results) / "chart" / cfg["run_id"]
    root.mkdir(parents=True, exist_ok=True)
    written = []
    if "iqrBars" in cfg["charts"]:
        by_chart = defaultdict(list)
        for c in cases:
            by_chart[(c["group"], c["groupLabel"], c["operation"], c["inputSize"])].append(c)
        for (group_id, group_label, operation, size), items in sorted(by_chart.items(), key=lambda kv: (kv[0][0], kv[0][2], kv[0][3] or 0)):
            written.append(chart_draw.iqr_bars(items, group_label, operation, size, root / f"{group_id}-{group_label}"))
    chart_report.write(root, cases, cfg, written)
    return root, written


def main():
    if len(sys.argv) != 5:
        sys.exit("usage: charts.py <benchmark.json> <prepared.yaml> <effective.yaml> <results>")
    root, written = build(*sys.argv[1:5])
    print(f"charts: {len(written)} written to {root}")


if __name__ == "__main__":
    main()
