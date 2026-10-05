"""The run-level charts: throughput against input size, latency of the slow primitives, and stability.

    analyze.py <benchmark.json> <out dir> [effective.yaml] [prepared.yaml]

Which of the three are drawn, and the CoV limit, come from analysis in effective.yaml (default: all, 5%).
The statistics are stats.py's, the same ones charts.py and its summary use, so no number here disagrees with them.
The IQR bars and the summary table are charts.py's.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import chart_draw  # noqa: E402
import chart_input  # noqa: E402
import chart_model  # noqa: E402

RUN_LEVEL = ("throughput", "latency", "stability")


def build(benchmark_file, out, effective_file="", prepared_file=""):
    raw, groups, effective = chart_input.load(benchmark_file, prepared_file, effective_file)
    cfg = chart_input.settings(effective)
    cases = [chart_model.summarize_case(c, groups, cfg) for c in raw]
    if any(c["group"] == chart_input.UNIDENTIFIED[0] for c in cases):
        print(f"warning: cases without a chartGroup in {prepared_file or 'no prepared.yaml'} are left off the group charts. "
              "Pass prepared.yaml, from a preparation run that writes chartGroup.", file=sys.stderr)
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    drawn = {
        "throughput": lambda: chart_draw.throughput(cases, out),
        "latency": lambda: chart_draw.latency(cases, out),
        "stability": lambda: chart_draw.stability(cases, out, cfg["limit"]),
    }
    written = [drawn[name]() for name in RUN_LEVEL if name in cfg["charts"] and cases]
    if cfg["countBars"]:       # additive: only when the run carries a count metric (allocationCount, a CPU event)
        by_id = {c["id"]: c for c in cases}
        for metric in chart_model.count_metrics(raw):
            pairs = [(r, by_id[r["id"]]) for r in (chart_model.summarize_count(c, groups, metric) for c in raw) if r]
            if pairs:
                written.append(chart_draw.count_vs_time(pairs, pairs[0][0]["label"], out, metric))
    return cases, cfg, written


def main():
    if not 3 <= len(sys.argv) <= 5:
        sys.exit("usage: analyze.py <benchmark.json> <out dir> [effective.yaml] [prepared.yaml]")
    cases, cfg, written = build(*sys.argv[1:5])
    unstable = [c for c in cases if c["noisy"]]
    print(f"cases={len(cases)} unstable(CoV>{cfg['limit']:g}%)={len(unstable)}")
    for c in sorted(unstable, key=lambda c: -c["ns"]["cov"])[:5]:
        print(f"  {c['id']}: CoV {c['ns']['cov']:.1%}, median {c['ns']['median']} ns")
    print("wrote", ", ".join(sorted(p.name for p in written)) or "nothing (analysis.charts names none of them)")


if __name__ == "__main__":
    main()
