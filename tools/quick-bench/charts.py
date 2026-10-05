"""IQR bar charts, one per chart group, operation and fixed input size, plus the summary and the data they plot.

    charts.py <benchmark.json> <prepared.yaml> <effective.yaml> <results>

Reads what the run already wrote and draws only what analysis.charts in effective.yaml names (default: all, of
which this file draws iqrBars). Statistics are taken on the measured ns/op, then shown as MB/s or us/op.
"""
import json
import pathlib
import re
import sys
from collections import defaultdict

import matplotlib
import yaml

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import stats  # noqa: E402

DEFAULT_CHARTS = ["iqrBars", "throughput", "latency", "stability"]
PAYLOAD_GROUPS = {1, 4, 5}      # symmetric-cipher, hash, mac: cost scales with the input, so MB/s means something
UNIDENTIFIED = (0, "unidentified")
NOISY_COLOR, CALM_COLOR = "#e07a1f", "#57068c"


def runs_of(case):
    metrics = case.get("metrics") or {}
    return (metrics.get("timeNs") or {}).get("runs") or case["nanosPerOperation"]


def size_label(size):
    return "n-a" if size is None else (f"{size}B" if size < 1024 else f"{size // 1024}KiB")


def short(algorithm):
    return re.sub(r"(PKCS5Padding|NoPadding|AndMGF1Padding|/ECB)", "", algorithm).strip("-/")


def load(benchmark_file, prepared_file, effective_file):
    benchmark = json.load(open(benchmark_file))
    prepared = yaml.safe_load(open(prepared_file).read()) if pathlib.Path(prepared_file).is_file() else {}
    effective = yaml.safe_load(open(effective_file).read()) if pathlib.Path(effective_file).is_file() else {}
    groups = {c["id"]: (c.get("chartGroupId", UNIDENTIFIED[0]), c.get("chartGroup", UNIDENTIFIED[1])) for c in (prepared or {}).get("cases", [])}
    return benchmark["cases"], groups, effective or {}


def settings(effective):
    analysis = effective.get("analysis") or {}
    statistic = analysis.get("statistic") or {}
    return {
        "charts": analysis["charts"] if "charts" in analysis else DEFAULT_CHARTS,
        "dir": analysis.get("dir"),
        "headline": statistic.get("headline", "auto"),
        "limit": float(statistic.get("meanUpToCovPercent", 5.0)),
        "run_id": effective.get("runId") or "adhoc",
    }


def summarize_case(case, groups, cfg):
    ns = stats.summarize(runs_of(case))
    group_id, group_label = groups.get(case["id"], UNIDENTIFIED)
    size = case.get("inputSize")
    if group_id in PAYLOAD_GROUPS and size:       # monotone, so the quartiles swap ends; the mean is the throughput of the mean time
        f = lambda t: size / t * 1000
        shown = dict(mean=f(ns["mean"]), median=f(ns["median"]), q1=f(ns["q3"]), q3=f(ns["q1"]))
        unit = "MB/s"
    else:
        f = lambda t: t / 1000
        shown = dict(mean=f(ns["mean"]), median=f(ns["median"]), q1=f(ns["q1"]), q3=f(ns["q3"]))
        unit = "us/op"
    return {
        "id": case["id"], "group": group_id, "groupLabel": group_label, "type": case["type"], "algorithm": case["algorithm"],
        "provider": case["provider"], "operation": case["operation"], "keySize": case.get("keySize"), "inputSize": size,
        "unit": unit, "ns": ns, "shown": shown, "lead": stats.headline(ns, cfg["headline"], cfg["limit"]),
        "noisy": ns["cov"] * 100 > cfg["limit"],
    }


def draw(items, group_id, group_label, operation, size, folder):
    items.sort(key=lambda c: (c["algorithm"], c["keySize"] or 0, c["provider"]))
    providers = {c["provider"] for c in items}
    labels = [short(c["algorithm"]) + (f"-{c['keySize']}" if c["keySize"] else "") + (f" ({c['provider'][:8]})" if len(providers) > 1 else "") for c in items]
    median = [c["shown"]["median"] for c in items]
    below = [c["shown"]["median"] - c["shown"]["q1"] for c in items]
    above = [c["shown"]["q3"] - c["shown"]["median"] for c in items]
    fig, ax = plt.subplots(figsize=(max(6, 0.55 * len(items) + 2), 4.2))
    ax.bar(range(len(items)), median, yerr=[below, above], capsize=3, width=0.7, ecolor="#2d0057",
           color=[NOISY_COLOR if c["noisy"] else CALM_COLOR for c in items])
    ax.scatter(range(len(items)), [c["shown"]["mean"] for c in items], marker="D", s=22, color="white", edgecolor="black", zorder=3, label="mean")
    ax.set_xticks(range(len(items)))
    ax.set_xticklabels(labels, rotation=60, ha="right", fontsize=7)
    ax.set_ylabel(items[0]["unit"])
    ax.grid(axis="y", alpha=.3)
    if items[0]["unit"] == "us/op" and max(median) / max(min(median), 1e-9) > 200:
        ax.set_yscale("log")
    runs = ",".join(str(n) for n in sorted({c["ns"]["n"] for c in items}))
    ax.set_title(f"{group_label} · {operation.lower().replace('-', ' ')} · input {size_label(size)}\n"
                 f"median, whiskers Q1-Q3, n={runs} runs; orange = CoV above the limit", fontsize=8)
    ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"iqr-bars_{operation.lower()}_input-{size_label(size)}.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def summary_table(cases):
    rows = ["| group | case | op | key | input | n | mean | sd (ns) | cov | median | q1 | q3 | qcd | headline | unit | flag |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in sorted(cases, key=lambda c: (c["group"], c["algorithm"], c["operation"], c["keySize"] or 0, c["inputSize"] or 0)):
        s, ns = c["shown"], c["ns"]
        rows.append(f"| {c['groupLabel']} | {short(c['algorithm'])} ({c['provider']}) | {c['operation']} | {c['keySize'] or '-'} | {size_label(c['inputSize'])} | {ns['n']} "
                    f"| {s['mean']:.4g} | {ns['sd']:.4g} | {ns['cov']:.1%} | {s['median']:.4g} | {s['q1']:.4g} | {s['q3']:.4g} | {ns['qcd']:.1%} | {c['lead']} | {c['unit']} | {'noisy' if c['noisy'] else ''} |")
    return "\n".join(rows) + "\n"


def build(benchmark_file, prepared_file, effective_file, results):
    raw, groups, effective = load(benchmark_file, prepared_file, effective_file)
    cfg = settings(effective)
    cases = [summarize_case(c, groups, cfg) for c in raw]
    ungrouped = sum(1 for c in cases if c["group"] == UNIDENTIFIED[0])
    if ungrouped:
        print(f"warning: {ungrouped} of {len(cases)} cases have no chartGroup in {prepared_file}; they are drawn as group 0. "
              "Run preparation again: groups come from the service type, not from this script.", file=sys.stderr)
    root = pathlib.Path(cfg["dir"].replace("<run-id>", cfg["run_id"])) if cfg["dir"] else pathlib.Path(results) / "chart" / cfg["run_id"]
    root.mkdir(parents=True, exist_ok=True)
    written = []
    if "iqrBars" in cfg["charts"]:
        by_chart = defaultdict(list)
        for c in cases:
            by_chart[(c["group"], c["groupLabel"], c["operation"], c["inputSize"])].append(c)
        for (group_id, group_label, operation, size), items in sorted(by_chart.items(), key=lambda kv: (kv[0][0], kv[0][2], kv[0][3] or 0)):
            written.append(draw(items, group_id, group_label, operation, size, root / f"{group_id}-{group_label}"))
    (root / "summary.md").write_text(summary_table(cases))
    (root / "chart-data.json").write_text(json.dumps(cases, indent=1))
    manifest = {
        "runId": cfg["run_id"], "cases": len(cases), "noisy": sum(c["noisy"] for c in cases),
        "headline": cfg["headline"], "meanUpToCovPercent": cfg["limit"], "charts": cfg["charts"],
        "definitions": {"cov": "sample sd / mean, as Jetpack", "qcd": "(Q3-Q1)/(Q3+Q1)", "quantile": "linear interpolation, as Jetpack"},
        "runsPerCase": sorted({c["ns"]["n"] for c in cases}),
        "files": sorted(str(p.relative_to(root)) for p in written) + ["summary.md", "chart-data.json"],
    }
    (root / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    return root, written


def main():
    if len(sys.argv) != 5:
        sys.exit("usage: charts.py <benchmark.json> <prepared.yaml> <effective.yaml> <results>")
    root, written = build(*sys.argv[1:5])
    print(f"charts: {len(written)} written to {root}")


if __name__ == "__main__":
    main()
