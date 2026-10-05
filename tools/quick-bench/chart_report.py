"""The text a run leaves beside its charts: the summary table, the data the charts plot, and the manifest."""
import json

import yaml

from chart_model import AUDIT_TOLERANCE, short, size_label


def summary_table(cases):
    rows = ["| group | case | op | key | input | n | mean | sd (ns) | cov | median | q1 | q3 | qcd | headline | unit | flag |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in sorted(cases, key=lambda c: (c["group"], c["algorithm"], c["operation"], c["keySize"] or 0, c["inputSize"] or 0)):
        s, ns = c["shown"], c["ns"]
        rows.append(f"| {c['groupLabel']} | {short(c['algorithm'])} ({c['provider']}) | {c['operation']} | {c['keySize'] or '-'} | {size_label(c['inputSize'])} | {ns['n']} "
                    f"| {s['mean']:.4g} | {ns['sd']:.4g} | {ns['cov']:.1%} | {s['median']:.4g} | {s['q1']:.4g} | {s['q3']:.4g} | {ns['qcd']:.1%} | {c['lead']} | {c['unit']} | {'noisy' if c['noisy'] else ''} |")
    return "\n".join(rows) + "\n"


def audit_summary(cases):
    checked = [c for c in cases if c["audit"]]
    worst = {k: max((c["audit"][k] for c in checked), default=0.0) for k in ("median", "min", "max", "cov")}
    return {"checked": len(checked), "tolerance": AUDIT_TOLERANCE, "maxRelativeDifference": worst,
            "mismatches": sorted(c["id"] for c in checked if max(c["audit"].values()) > AUDIT_TOLERANCE)}


def manifest(cases, cfg, written, root):
    return {
        "runId": cfg["run_id"], "cases": len(cases), "noisy": sum(c["noisy"] for c in cases),
        "headline": cfg["headline"], "meanUpToCovPercent": cfg["limit"], "charts": cfg["charts"],
        "definitions": {"cov": "sample sd / mean, as Jetpack", "qcd": "(Q3-Q1)/(Q3+Q1)", "quantile": "linear interpolation, as Jetpack"},
        "runsPerCase": sorted({c["ns"]["n"] for c in cases}),
        "auditAgainstJetpack": audit_summary(cases),
        "files": sorted(str(p.relative_to(root)) for p in written) + ["summary.md", "chart-data.json"],
    }


def write(root, cases, cfg, written):
    (root / "summary.md").write_text(summary_table(cases))
    (root / "chart-data.json").write_text(json.dumps(cases, indent=1))
    (root / "manifest.yaml").write_text(yaml.safe_dump(manifest(cases, cfg, written, root), sort_keys=False))
