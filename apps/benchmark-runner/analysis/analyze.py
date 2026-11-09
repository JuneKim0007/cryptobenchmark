"""summary.md and the run-level charts: throughput, latency, stability, and a count metric against time.

    analyze.py <benchmark.json> <out dir> [effective.yaml] [prepared.yaml]

Statistics are stats.py's, taken on the runs the outlier gate keeps. analysis.charts in effective.yaml picks the
charts and its meanUpToCovPercent is the stability limit (default: all, 5%). The IQR bars are charts.py's.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import chart_input  # noqa: E402
import chart_model  # noqa: E402
import display_units  # noqa: E402
import stats  # noqa: E402
from outliers import split  # noqa: E402
from cryptobench import paths

RUN_LEVEL = ("throughput", "latency", "stability")


def summarize(case, groups, cfg):
    runs, removed = split(chart_model.runs_of(case))
    ns = stats.summarize(runs)
    size, units = case["inputSize"], cfg["units"]
    def rate(nanos): return display_units.throughput(nanos, size, units)
    group, group_label = groups.get(case["id"], chart_input.UNIDENTIFIED)
    return dict(case, ns=ns, mean=ns["mean"], removed=len(removed), median=ns["median"], cov=ns["cov"],
                latency=display_units.latency(ns["mean"], units), rate=rate(ns["mean"]), rate_min=rate(ns["max"]),
                rate_max=rate(ns["min"]), group=group, groupLabel=group_label, noisy=ns["cov"] * 100 > cfg["limit"])


def estimated_note(raw):
    sources = chart_model.estimated_energy(raw)
    return f"energyJ is estimated by {', '.join(sources)}, not measured." if sources else None


def _cleaning_cells(row):
    cleaned = chart_model.cleaning(row)
    return f"{cleaned['pauseMs']:.1f} | {cleaned['itersWithGc']:.0%}" if cleaned else "- | -"


def summary(rows, out, units, note=None):
    lines = [f"| case | op | key | input | {display_units.latency_label(units)} | {units['throughput']} | CoV | outliers | GC pause (ms/iter) | iters with a GC |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["type"], r["algorithm"], r["operation"], r["inputSize"] or 0, r.get("variant") or "")):
        lines.append(f"| {r['algorithm']} | {r['operation']}{chart_model.variant(r)} | {r['keySize'] or '-'} | {r['inputSize'] or '-'} "
                     f"| {display_units.number(r['latency'])} | {display_units.number(r['rate'])} | {r['cov']:.1%} | {r['removed']} | {_cleaning_cells(r)} |")
    paths.Analysis(out).summary.write_text("\n".join(lines + (["", note] if note else [])) + "\n")
    if note:
        print(f"note: {note}")


def build(benchmark_file, out, effective_file="", prepared_file=""):
    raw, groups, effective = chart_input.load(benchmark_file, prepared_file, effective_file)
    cfg = chart_input.settings(effective)
    rows = [summarize(c, groups, cfg) for c in raw]
    if any(r["group"] == chart_input.UNIDENTIFIED[0] for r in rows):
        print(f"warning: cases without a chartGroup in {prepared_file or 'no prepared.yaml'} are left off the group charts. "
              "Pass prepared.yaml, from a preparation run that writes chartGroup.", file=sys.stderr)
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    summary(rows, out, cfg["units"], estimated_note(raw))
    # after summary.md: without matplotlib the table is still written
    import chart_draw
    drawn = {
        "throughput": lambda: chart_draw.throughput(rows, out, cfg["units"]),
        "latency": lambda: chart_draw.latency(rows, out, cfg["units"]),
        "stability": lambda: chart_draw.stability(rows, out, cfg["limit"]),
    }
    written = [drawn[name]() for name in RUN_LEVEL if name in cfg["charts"] and rows]
    if cfg["countBars"]:
        by_id = {r["id"]: r for r in rows}
        for metric in chart_model.count_metrics(raw):
            pairs = [(c, by_id[c["id"]]) for c in (chart_model.summarize_count(c, groups, metric) for c in raw) if c]
            if pairs:
                written.append(chart_draw.count_vs_time(pairs, pairs[0][0]["label"], out, metric, cfg["units"]))
    return rows, cfg, written


def main():
    if not 3 <= len(sys.argv) <= 5:
        sys.exit("usage: analyze.py <benchmark.json> <out dir> [effective.yaml] [prepared.yaml]")
    rows, cfg, written = build(*sys.argv[1:5])
    unstable = [r for r in rows if r["noisy"]]
    print(f"cases={len(rows)} unstable(CoV>{cfg['limit']:g}%)={len(unstable)}")
    for r in sorted(unstable, key=lambda r: -r["cov"])[:5]:
        print(f"  {r['id']}: CoV {r['cov']:.1%}, {display_units.number(r['latency'])} {display_units.latency_label(cfg['units'])}, "
              f"{r['removed']} outliers removed")
    print("wrote", ", ".join(sorted(["summary.md"] + [p.name for p in written])))


if __name__ == "__main__":
    main()
