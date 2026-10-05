"""The text a run leaves beside its charts: the summary table, the data the charts plot, and the manifest."""
import json

import yaml

from chart_model import AUDIT_TOLERANCE, short, size_label


def summary_table(cases):
    rows = ["| group | case | op | key | input | n | unit | mean | median | q1 | q3 | cov | qcd | headline | flag |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in sorted(cases, key=lambda c: (c["group"], c["algorithm"], c["operation"], c["keySize"] or 0, c["inputSize"] or 0)):
        s, ns = c["shown"], c["ns"]
        rows.append(f"| {c['groupLabel']} | {short(c['algorithm'])} ({c['provider']}) | {c['operation']} | {c['keySize'] or '-'} | {size_label(c['inputSize'])} | {ns['n']} "
                    f"| {c['unit']} | {s['mean']:.4g} | {s['median']:.4g} | {s['q1']:.4g} | {s['q3']:.4g} | {ns['cov']:.1%} | {ns['qcd']:.1%} | {c['lead']} | {'noisy' if c['noisy'] else ''} |")
    return "\n".join(rows) + "\n"


def audit_summary(cases):
    checked = [c for c in cases if c["audit"]]
    worst = {k: max((c["audit"][k] for c in checked), default=0.0) for k in ("median", "min", "max", "cov")}
    return {"checked": len(checked), "tolerance": AUDIT_TOLERANCE, "maxRelativeDifference": worst,
            "mismatches": sorted(c["id"] for c in checked if max(c["audit"].values()) > AUDIT_TOLERANCE)}


def count_table(rows):
    """Median and observed range of one count metric per case. No IQR/CoV: with n this small they would be noise."""
    lines = ["| group | case | op | key | input | n | median | min | max | runs |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["group"], r["algorithm"], r["operation"], r["keySize"] or 0, r["inputSize"] or 0)):
        s = r["stats"]
        lines.append(f"| {r['groupLabel']} | {short(r['algorithm'])} ({r['provider']}) | {r['operation']} | {r['keySize'] or '-'} | {size_label(r['inputSize'])} "
                     f"| {s['n']} | {s['median']:.6g} | {s['min']:.6g} | {s['max']:.6g} | {' '.join(f'{v:.6g}' for v in r['runs'])} |")
    return "\n".join(lines) + "\n"


def manifest(cases, cfg, written, root, counts=None):
    extra = {"countMetrics": {m: {"label": rows[0]["label"], "cases": len(rows), "runsPerCase": sorted({r["stats"]["n"] for r in rows})}
                              for m, rows in counts.items()}} if counts else {}
    return {**extra,
        "runId": cfg["run_id"], "cases": len(cases), "noisy": sum(c["noisy"] for c in cases),
        "headline": cfg["headline"], "meanUpToCovPercent": cfg["limit"], "charts": cfg["charts"],
        "definitions": {"cov": "sample sd / mean, as Jetpack", "qcd": "(Q3-Q1)/(Q3+Q1)", "quantile": "linear interpolation, as Jetpack"},
        "runsPerCase": sorted({c["ns"]["n"] for c in cases}),
        "auditAgainstJetpack": audit_summary(cases),
        "files": sorted(str(p.relative_to(root)) for p in written) + ["summary.md", "chart-data.json"],
    }


def write(root, cases, cfg, written, counts=None):
    """With no count metric the three files are exactly what they were; each count metric adds a table and a data file."""
    text = summary_table(cases)
    for metric, rows in (counts or {}).items():
        text += f"\n## {metric}: {rows[0]['label']} (n = {','.join(str(n) for n in sorted({r['stats']['n'] for r in rows}))} runs per case)\n\n" + count_table(rows)
        (root / f"chart-data-{metric}.json").write_text(json.dumps(rows, indent=1))
    (root / "summary.md").write_text(text)
    (root / "chart-data.json").write_text(json.dumps(cases, indent=1))
    (root / "manifest.yaml").write_text(yaml.safe_dump(manifest(cases, cfg, written, root, counts), sort_keys=False))
