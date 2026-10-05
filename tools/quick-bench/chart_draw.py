"""Drawing: the only file that imports matplotlib."""
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
