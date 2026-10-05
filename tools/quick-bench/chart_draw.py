"""Drawing: the only file that imports matplotlib. One function per chart kind named in analysis.charts."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from chart_model import short, size_label  # noqa: E402

NOISY_COLOR, CALM_COLOR = "#e07a1f", "#57068c"


def iqr_bars(items, group_label, operation, size, folder):
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


def _number(value):
    return f"{value:.0f}" if float(value).is_integer() else f"{value:.3g}"


def count_bars(items, metric_label, group_label, operation, size, folder, metric):
    """Median of a count metric with min-max whiskers. Few runs (Jetpack's allocation pass is 5) make quartiles meaningless."""
    items.sort(key=lambda c: (c["algorithm"], c["keySize"] or 0, c["provider"]))
    providers = {c["provider"] for c in items}
    labels = [short(c["algorithm"]) + (f"-{c['keySize']}" if c["keySize"] else "") + (f" ({c['provider'][:8]})" if len(providers) > 1 else "") for c in items]
    median = [c["stats"]["median"] for c in items]
    below = [c["stats"]["median"] - c["stats"]["min"] for c in items]
    above = [c["stats"]["max"] - c["stats"]["median"] for c in items]
    fig, ax = plt.subplots(figsize=(max(6, 0.55 * len(items) + 2), 4.2))
    ax.bar(range(len(items)), median, yerr=[below, above], capsize=3, width=0.7, ecolor="#2d0057", color=CALM_COLOR)
    top = max(c["stats"]["max"] for c in items)
    for i, c in enumerate(items):
        ax.text(i, c["stats"]["max"] + 0.02 * max(top, 1), _number(c["stats"]["median"]), ha="center", va="bottom", fontsize=7)
    ax.set_xticks(range(len(items)))
    ax.set_xticklabels(labels, rotation=60, ha="right", fontsize=7)
    ax.set_ylabel(metric_label)
    ax.set_ylim(0, max(top, 1) * 1.12)
    ax.grid(axis="y", alpha=.3)
    runs = ",".join(str(n) for n in sorted({c["stats"]["n"] for c in items}))
    ax.set_title(f"{group_label} · {operation.lower().replace('-', ' ')} · input {size_label(size)} · {metric_label}\n"
                 f"median, whiskers min-max, n={runs} runs (too few for quartiles, so no IQR)", fontsize=8)
    fig.tight_layout()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{metric}-bars_{operation.lower()}_input-{size_label(size)}.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def count_vs_time(pairs, metric_label, out, metric):
    """Median count per call against median time per call, one point per case, both axes log; each point carries its own n."""
    fig, ax = plt.subplots(figsize=(8, 5.5))
    groups = sorted({c["groupLabel"] for c, _ in pairs})
    colors = plt.get_cmap("tab10")
    for i, name in enumerate(groups):
        pts = [(c, t) for c, t in pairs if c["groupLabel"] == name]
        ax.scatter([t["ns"]["median"] / 1000 for _, t in pts], [max(c["stats"]["median"], 0.5) for c, _ in pts], s=22, color=colors(i % 10), label=name, alpha=.8)
    ax.set_xscale("log")
    ax.set_yscale("log")
    zero = sum(1 for c, _ in pairs if c["stats"]["median"] == 0)
    ax.set_xlabel(f"median time, us/op (n={','.join(str(n) for n in sorted({t['ns']['n'] for _, t in pairs}))} runs)")
    ax.set_ylabel(f"median {metric_label} (n={','.join(str(n) for n in sorted({c['stats']['n'] for c, _ in pairs}))} runs; zero medians drawn at 0.5)")
    ax.set_title(f"{metric_label} against time, {len(pairs)} cases" + (f"; {zero} with a median of 0" if zero else ""), fontsize=10)
    ax.grid(alpha=.3, which="both")
    ax.legend(fontsize=7)
    fig.tight_layout()
    path = out / f"{metric}-vs-time.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def label(case):
    return case["algorithm"] + (f"-{case['keySize']}" if case["keySize"] else "")


def throughput(cases, out):
    """MB/s against input size for the groups whose cost scales with the input; the band is the observed min-max."""
    panels = [("Symmetric ciphers", {1}), ("Hash / MAC", {4, 5})]
    runs = ",".join(str(n) for n in sorted({c["ns"]["n"] for c in cases}))
    fig, axes = plt.subplots(1, len(panels), figsize=(12, 5), sharey=True)
    for ax, (title, groups) in zip(axes, panels):
        series = {}
        for c in cases:
            if c["group"] in groups and c["unit"] == "MB/s" and c["operation"] in ("ENCRYPT", "DIGEST", "COMPUTE_MAC"):
                series.setdefault(label(c), []).append(c)
        for name, points in sorted(series.items()):
            points.sort(key=lambda c: c["inputSize"])
            xs = [c["inputSize"] for c in points]
            line, = ax.plot(xs, [c["shown"]["median"] for c in points], marker="o", label=name)
            ax.fill_between(xs, [c["shown"]["min"] for c in points], [c["shown"]["max"] for c in points], color=line.get_color(), alpha=0.15)
        ax.set_xscale("log", base=2)
        ax.set_xlabel("input size (bytes)")
        ax.set_title(title)
        ax.grid(alpha=.3)
        if series:
            ax.legend(fontsize=8)
    axes[0].set_ylabel(f"MB/s (line = median of {runs} runs, band = observed min-max)")
    fig.suptitle("Throughput vs input size, by chart group")
    fig.tight_layout()
    path = out / "throughput.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def latency(cases, out):
    """Median time of the operations whose cost does not scale with a payload: asymmetric, signatures, key generation."""
    slow = sorted((c for c in cases if c["group"] in {2, 3, 8, 9}), key=lambda c: c["shown"]["median"])
    plt.figure(figsize=(8, max(3, 0.28 * len(slow) + 1.5)))
    names = [f"{label(c)} {c['operation'].lower()}" + (f" {c['inputSize']}B" if c["inputSize"] else "") for c in slow]
    plt.barh(names, [c["shown"]["median"] for c in slow], color="#4c72b0")
    plt.xscale("log")
    plt.xlabel("median us/op (log)")
    plt.title("Asymmetric operations, signatures and key generation")
    plt.grid(axis="x", alpha=.3)
    plt.tight_layout()
    path = out / "latency.png"
    plt.savefig(path, dpi=140, bbox_inches="tight")
    plt.close()
    return path


def stability(cases, out, limit_percent):
    """How many cases fall at each CoV level, with the configured limit marked."""
    covs = [c["ns"]["cov"] * 100 for c in cases]
    unstable = [c for c in cases if c["noisy"]]
    runs = ",".join(str(n) for n in sorted({c["ns"]["n"] for c in cases}))
    plt.figure(figsize=(8, 4.5))
    plt.hist(covs, bins=[0, 1, 2, 3, 5, 8, 13, 21, max(21, max(covs) + 1)], color="#4c72b0", edgecolor="white")
    plt.axvline(limit_percent, color="crimson", linestyle="--", label=f"{limit_percent:g}% limit")
    plt.xlabel(f"coefficient of variation % (sample sd / mean; one case = {runs} runs)")
    plt.ylabel("number of cases")
    plt.title(f"Run-to-run stability: {len(cases) - len(unstable)}/{len(cases)} cases within the {limit_percent:g}% limit")
    if unstable:
        worst = sorted(unstable, key=lambda c: -c["ns"]["cov"])[:5]
        note = "Worst offenders:\n" + "\n".join(f"{label(c)} {c['operation'].lower()}: {c['ns']['cov']:.0%}" for c in worst)
        plt.gca().text(0.98, 0.95, note, transform=plt.gca().transAxes, fontsize=8, va="top", ha="right", family="monospace",
                       bbox=dict(boxstyle="round", facecolor="#fde9c8", edgecolor="#8a4b00"))
    plt.legend()
    plt.grid(axis="y", alpha=.3)
    plt.tight_layout()
    path = out / "stability.png"
    plt.savefig(path, dpi=140)
    plt.close()
    return path
