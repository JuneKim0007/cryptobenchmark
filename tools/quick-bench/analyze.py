"""summary.md and the run-level charts: throughput, latency, stability, and a count metric against time.

    analyze.py <benchmark.json> <out dir> [effective.yaml] [prepared.yaml]

Statistics are stats.py's, taken on the runs the outlier gate keeps. analysis.charts in effective.yaml picks the
charts and its meanUpToCovPercent is the stability limit (default: all, 5%). The IQR bars are charts.py's.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import chart_draw  # noqa: E402
import chart_input  # noqa: E402
import chart_model  # noqa: E402
import stats  # noqa: E402
from outliers import split  # noqa: E402

RUN_LEVEL = ("throughput", "latency", "stability")


def summarize(case, groups, limit):
    runs, removed = split(chart_model.runs_of(case))
    ns = stats.summarize(runs)
    size = case["inputSize"]
    def mbps_of(nanos): return (size / nanos * 1000) if size and nanos else None
    group, group_label = groups.get(case["id"], chart_input.UNIDENTIFIED)
    return dict(case, ns=ns, mean=ns["mean"], removed=len(removed), median=ns["median"], ops=1e9 / ns["mean"], cov=ns["cov"],
                mbps=mbps_of(ns["mean"]), mbps_min=mbps_of(ns["max"]), mbps_max=mbps_of(ns["min"]),
                group=group, groupLabel=group_label, noisy=ns["cov"] * 100 > limit)


def summary(rows, out):
    lines = ["| case | op | key | input | ops/s | MB/s | CoV | outliers |", "|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["type"], r["algorithm"], r["operation"], r["inputSize"] or 0)):
        mbps = f"{r['mbps']:,.0f}" if r["mbps"] else "-"
        lines.append(f"| {r['algorithm']} | {r['operation']} | {r['keySize'] or '-'} | {r['inputSize'] or '-'} | {r['ops']:,.0f} | {mbps} | {r['cov']:.1%} | {r['removed']} |")
    (out / "summary.md").write_text("\n".join(lines) + "\n")


def build(benchmark_file, out, effective_file="", prepared_file=""):
    raw, groups, effective = chart_input.load(benchmark_file, prepared_file, effective_file)
    cfg = chart_input.settings(effective)
    rows = [summarize(c, groups, cfg["limit"]) for c in raw]
    if any(r["group"] == chart_input.UNIDENTIFIED[0] for r in rows):
        print(f"warning: cases without a chartGroup in {prepared_file or 'no prepared.yaml'} are left off the group charts. "
              "Pass prepared.yaml, from a preparation run that writes chartGroup.", file=sys.stderr)
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    summary(rows, out)
    drawn = {
        "throughput": lambda: chart_draw.throughput(rows, out),
        "latency": lambda: chart_draw.latency(rows, out),
        "stability": lambda: chart_draw.stability(rows, out, cfg["limit"]),
    }
    written = [drawn[name]() for name in RUN_LEVEL if name in cfg["charts"] and rows]
    if cfg["countBars"]:
        by_id = {r["id"]: r for r in rows}
        for metric in chart_model.count_metrics(raw):
            pairs = [(c, by_id[c["id"]]) for c in (chart_model.summarize_count(c, groups, metric) for c in raw) if c]
            if pairs:
                written.append(chart_draw.count_vs_time(pairs, pairs[0][0]["label"], out, metric))
    return rows, cfg, written


def main():
    if not 3 <= len(sys.argv) <= 5:
        sys.exit("usage: analyze.py <benchmark.json> <out dir> [effective.yaml] [prepared.yaml]")
    rows, cfg, written = build(*sys.argv[1:5])
    unstable = [r for r in rows if r["noisy"]]
    print(f"cases={len(rows)} unstable(CoV>{cfg['limit']:g}%)={len(unstable)}")
    for r in sorted(unstable, key=lambda r: -r["cov"])[:5]:
        print(f"  {r['id']}: CoV {r['cov']:.1%}, {r['ops']:,.0f} ops/s, {r['removed']} outliers removed")
    print("wrote", ", ".join(sorted(["summary.md"] + [p.name for p in written])))


if __name__ == "__main__":
    main()
