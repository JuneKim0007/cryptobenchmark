import json, statistics, pathlib, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from outliers import split  # noqa: E402

source = json.load(open(sys.argv[1])); out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
rows = []
for c in source["cases"]:
    runs, removed = split(((c.get("metrics") or {}).get("timeNs") or {}).get("runs") or c["nanosPerOperation"])
    mean, median = statistics.fmean(runs), statistics.median(runs)
    cov = statistics.stdev(runs) / mean if mean and len(runs) > 1 else 0
    mn, mx = min(runs), max(runs)
    def mbps_of(nanos): return (c["inputSize"] / nanos * 1000) if c["inputSize"] and nanos else None
    rows.append(dict(c, mean=mean, removed=len(removed), median=median, ops=1e9 / mean, p90=sorted(runs)[int(0.9 * (len(runs) - 1))], min=mn, max=mx, cov=cov,
                     mbps=mbps_of(mean), mbps_min=mbps_of(mx), mbps_max=mbps_of(mn)))

def label(r):
    key = f"-{r['keySize']}" if r["keySize"] else ""
    return f"{r['algorithm']}{key}"

lines = ["| case | op | key | input | ops/s | MB/s | CoV | outliers |", "|---|---|---|---|---|---|---|---|"]
for r in sorted(rows, key=lambda r: (r["type"], r["algorithm"], r["operation"], r["inputSize"] or 0)):
    mbps = f"{r['mbps']:,.0f}" if r["mbps"] else "-"
    lines.append(f"| {r['algorithm']} | {r['operation']} | {r['keySize'] or '-'} | {r['inputSize'] or '-'} | {r['ops']:,.0f} | {mbps} | {r['cov']:.1%} | {r['removed']} |")
(out / "summary.md").write_text("\n".join(lines) + "\n")

# Cipher covers both AES and RSA, so asymmetric is excluded by name: RSA has one
# fixed-size block, not a size sweep.
ASYMMETRIC_PREFIXES = ("RSA", "EC")
def is_symmetric_cipher(r):
    return r["type"] == "Cipher" and not r["algorithm"].startswith(ASYMMETRIC_PREFIXES)

GROUPS = [
    ("Symmetric ciphers", is_symmetric_cipher),
    ("Hash / MAC", lambda r: r["type"] in ("MessageDigest", "Mac")),
]
fig, axes = plt.subplots(1, len(GROUPS), figsize=(12, 5), sharey=True)
for ax, (title, matches) in zip(axes, GROUPS):
    series = {}
    for r in rows:
        if r["mbps"] and r["operation"] in ("ENCRYPT", "DIGEST", "COMPUTE_MAC") and matches(r):
            series.setdefault(label(r), []).append(r)
    for name, pts in sorted(series.items()):
        pts.sort(key=lambda r: r["inputSize"])
        xs = [r["inputSize"] for r in pts]
        med = [r["mbps"] for r in pts]
        lo = [r["mbps_min"] for r in pts]
        hi = [r["mbps_max"] for r in pts]
        line, = ax.plot(xs, med, marker="o", label=name)
        ax.fill_between(xs, lo, hi, color=line.get_color(), alpha=0.15)
    ax.set_xscale("log", base=2)
    ax.set_xlabel("input size (bytes)")
    ax.set_title(title)
    ax.grid(alpha=.3)
    ax.legend(fontsize=8)
axes[0].set_ylabel("MB/s")
fig.suptitle("Throughput vs input size")
fig.tight_layout()
fig.savefig(out / "throughput.png", dpi=140)
plt.close(fig)

plt.figure(figsize=(8, 4.5))
slow = [r for r in rows if r["type"] in ("Signature", "KeyPairGenerator", "KeyGenerator") or r["algorithm"].startswith("RSA")]
slow.sort(key=lambda r: -r["ops"])
names = [f"{label(r)} {r['operation'].lower()}" + (f" {r['inputSize']}B" if r["inputSize"] else "") for r in slow]
plt.barh(names, [r["ops"] for r in slow], color="#4c72b0")
plt.xscale("log"); plt.xlabel("ops/s (log)"); plt.title("Asymmetric operations and key generation")
plt.grid(axis="x", alpha=.3); plt.tight_layout(); plt.savefig(out / "latency.png", dpi=140, bbox_inches="tight"); plt.close()

covs_pct = [r["cov"] * 100 for r in rows]
unstable = [r for r in rows if r["cov"] > 0.05]
plt.figure(figsize=(8, 4.5))
bins = [0, 1, 2, 3, 5, 8, 13, 21, max(21, max(covs_pct) + 1)]
plt.hist(covs_pct, bins=bins, color="#4c72b0", edgecolor="white")
plt.axvline(5, color="crimson", linestyle="--", label="5% gate")
plt.xlabel("CoV (%)")
plt.ylabel("number of cases")
plt.title(f"Run-to-run stability: {len(rows) - len(unstable)}/{len(rows)} cases under the 5% gate")
if unstable:
    worst = sorted(unstable, key=lambda r: -r["cov"])[:5]
    note = "Worst offenders:\n" + "\n".join(f"{label(r)} {r['operation'].lower()}: {r['cov']:.0%}" for r in worst)
    plt.gca().text(0.98, 0.95, note, transform=plt.gca().transAxes, fontsize=8,
                    va="top", ha="right", family="monospace",
                    bbox=dict(boxstyle="round", facecolor="#fde9c8", edgecolor="#8a4b00"))
plt.legend(); plt.grid(axis="y", alpha=.3); plt.tight_layout(); plt.savefig(out / "stability.png", dpi=140); plt.close()
print(f"cases={len(rows)} unstable(CoV>5%)={len(unstable)}")
for r in sorted(unstable, key=lambda r: -r["cov"])[:5]:
    print(f"  {r['id']}: CoV {r['cov']:.1%}, {r['ops']:,.0f} ops/s, {r['removed']} outliers removed")
print("wrote", ", ".join(sorted(p.name for p in out.iterdir())))
