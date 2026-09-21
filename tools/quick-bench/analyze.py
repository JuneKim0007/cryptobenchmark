import json, statistics, pathlib, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

source = json.load(open(sys.argv[1])); out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
rows = []
for c in source["cases"]:
    runs = c["nanosPerOperation"]
    median = statistics.median(runs)
    cov = statistics.pstdev(runs) / median if median else 0
    rows.append(dict(c, median=median, p90=sorted(runs)[int(0.9 * (len(runs) - 1))], min=min(runs), cov=cov,
                     mbps=(c["inputSize"] / median * 1000) if c["inputSize"] and median else None))

def label(r):
    key = f"-{r['keySize']}" if r["keySize"] else ""
    return f"{r['algorithm']}{key}"

lines = ["| case | op | key | input | median ns | p90 ns | CoV | MB/s |", "|---|---|---|---|---|---|---|---|"]
for r in sorted(rows, key=lambda r: (r["type"], r["algorithm"], r["operation"], r["inputSize"] or 0)):
    lines.append(f"| {r['algorithm']} | {r['operation']} | {r['keySize'] or '-'} | {r['inputSize'] or '-'} | {r['median']:,} | {r['p90']:,} | {r['cov']:.1%} | {f'{r
["mbps"]:.0f}' if r['mbps'] else '-'} |")
(out / "summary.md").write_text("\n".join(lines) + "\n")

# 1. throughput vs input size
plt.figure(figsize=(8, 5))
series = {}
for r in rows:
    if r["mbps"] and r["operation"] in ("ENCRYPT", "DIGEST", "COMPUTE_MAC") and r["type"] != "Signature":
        series.setdefault(label(r), []).append((r["inputSize"], r["mbps"]))
for name, points in sorted(series.items()):
    points.sort()
    plt.plot([p[0] for p in points], [p[1] for p in points], marker="o", label=name)
plt.xscale("log", base=2); plt.xlabel("input size (bytes)"); plt.ylabel("MB/s"); plt.title("Throughput vs input size (JVM, SunJCE/SUN)")
plt.grid(alpha=.3); plt.legend(fontsize=8); plt.tight_layout(); plt.savefig(out / "throughput.png", dpi=140); plt.close()

# 2. latency of asymmetric and key generation
plt.figure(figsize=(8, 4.5))
slow = [r for r in rows if r["type"] in ("Signature", "KeyPairGenerator", "KeyGenerator") or r["algorithm"].startswith("RSA")]
slow.sort(key=lambda r: r["median"])
names = [f"{label(r)} {r['operation'].lower()}" + (f" {r['inputSize']}B" if r["inputSize"] else "") for r in slow]
plt.barh(names, [r["median"] for r in slow], color="#4c72b0")
plt.xscale("log"); plt.xlabel("median ns/op (log)"); plt.title("Asymmetric operations and key generation")
plt.grid(axis="x", alpha=.3); plt.tight_layout(); plt.savefig(out / "latency.png", dpi=140, bbox_inches="tight"); plt.close()

# 3. stability gate
plt.figure(figsize=(7, 4))
covs = sorted(r["cov"] for r in rows)
plt.plot(range(len(covs)), [c * 100 for c in covs], marker=".", linestyle="none")
plt.axhline(5, color="crimson", linestyle="--", label="5% gate")
plt.xlabel("case (sorted)"); plt.ylabel("coefficient of variation %"); plt.title("Run-to-run stability")
plt.legend(); plt.grid(alpha=.3); plt.tight_layout(); plt.savefig(out / "stability.png", dpi=140); plt.close()

unstable = [r for r in rows if r["cov"] > 0.05]
print(f"cases={len(rows)} unstable(CoV>5%)={len(unstable)}")
for r in sorted(unstable, key=lambda r: -r["cov"])[:5]:
    print(f"  {r['id']}: CoV {r['cov']:.1%}, median {r['median']} ns")
print("wrote", ", ".join(sorted(p.name for p in out.iterdir())))
