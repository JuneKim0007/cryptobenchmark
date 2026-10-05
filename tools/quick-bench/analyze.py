import json, statistics, pathlib, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

source = json.load(open(sys.argv[1])); out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
rows = []
for c in source["cases"]:
    runs = c["nanosPerOperation"]
    median = statistics.median(runs)
    cov = statistics.pstdev(runs) / median if median else 0
    mn, mx = min(runs), max(runs)
    def mbps_of(nanos): return (c["inputSize"] / nanos * 1000) if c["inputSize"] and nanos else None
    rows.append(dict(c, median=median, p90=sorted(runs)[int(0.9 * (len(runs) - 1))], min=mn, max=mx, cov=cov,
                     mbps=mbps_of(median), mbps_min=mbps_of(mx), mbps_max=mbps_of(mn)))

def label(r):
    key = f"-{r['keySize']}" if r["keySize"] else ""
    return f"{r['algorithm']}{key}"

lines = ["| case | op | key | input | median ns | p90 ns | CoV | MB/s |", "|---|---|---|---|---|---|---|---|"]
for r in sorted(rows, key=lambda r: (r["type"], r["algorithm"], r["operation"], r["inputSize"] or 0)):
    lines.append(f"| {r['algorithm']} | {r['operation']} | {r['keySize'] or '-'} | {r['inputSize'] or '-'} | {r['median']:,} | {r['p90']:,} | {r['cov']:.1%} | {f'{r
["mbps"]:.0f}' if r['mbps'] else '-'} |")
(out / "summary.md").write_text("\n".join(lines) + "\n")

# 1. throughput vs input size, grouped by primitive type (not mixed with asymmetric --
#    RSA has one fixed-size block, not a size sweep, so it never belongs on this chart).
#    Shaded band = observed min/max across the sampled runs, not just the median line.
# JCA's Cipher engine class covers both symmetric (AES, ChaCha20) and asymmetric
# (RSA) algorithms under the same "type": "Cipher" -- type alone can't separate them.
# RSA has one fixed-size block regardless of "input size", so it's excluded by name.
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
axes[0].set_ylabel("MB/s (line = median of 5 runs, band = observed min–max)")
fig.suptitle("Throughput vs input size, by primitive type (JVM, SunJCE/SUN)")
fig.tight_layout()
fig.savefig(out / "throughput.png", dpi=140)
plt.close(fig)

# 2. latency of asymmetric and key generation
plt.figure(figsize=(8, 4.5))
slow = [r for r in rows if r["type"] in ("Signature", "KeyPairGenerator", "KeyGenerator") or r["algorithm"].startswith("RSA")]
slow.sort(key=lambda r: r["median"])
names = [f"{label(r)} {r['operation'].lower()}" + (f" {r['inputSize']}B" if r["inputSize"] else "") for r in slow]
plt.barh(names, [r["median"] for r in slow], color="#4c72b0")
plt.xscale("log"); plt.xlabel("median ns/op (log)"); plt.title("Asymmetric operations and key generation")
plt.grid(axis="x", alpha=.3); plt.tight_layout(); plt.savefig(out / "latency.png", dpi=140, bbox_inches="tight"); plt.close()

# 3. stability gate -- a histogram of how many cases fall at each CoV level, not a
#    sorted-index scatter (sorting-then-plotting-by-index makes an unrelated set of
#    values look like an upward trend, which it isn't: there's no run-order or time
#    axis here at all, just "how many of the 56 cases had this much run-to-run spread").
covs_pct = [r["cov"] * 100 for r in rows]
unstable = [r for r in rows if r["cov"] > 0.05]
plt.figure(figsize=(8, 4.5))
bins = [0, 1, 2, 3, 5, 8, 13, 21, max(21, max(covs_pct) + 1)]
plt.hist(covs_pct, bins=bins, color="#4c72b0", edgecolor="white")
plt.axvline(5, color="crimson", linestyle="--", label="5% gate")
plt.xlabel("coefficient of variation % (one case = 5 repeated runs)")
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
    print(f"  {r['id']}: CoV {r['cov']:.1%}, median {r['median']} ns")
print("wrote", ", ".join(sorted(p.name for p in out.iterdir())))
