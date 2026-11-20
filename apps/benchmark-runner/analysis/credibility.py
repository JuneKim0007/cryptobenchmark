"""credibility.md, credibility.json and qq/<case>.png: per case and per fixed/notFixed pair, statistics over one value per process.

    credibility.py <out dir> <benchmark.json of each process>...
"""
import json
import pathlib
import statistics
import sys

from chart_input import process_cases
from chart_model import ENERGY, TIME
from cryptobench.shared import paths
from cryptobench.shared.paths.names import VARIANT_FIXED, VARIANT_NOT_FIXED
from cryptobench.shared.stats import descriptive, inference
from cryptobench.shared.stats.equations import median_ranks
from cryptobench.shared.stats.units import number

METRICS = {TIME: "ns/op", ENERGY: "J/op"}
MIN_WITHIN_NORMALITY = 8        # fewer samples in a process make its own Q-Q score mean little
DRIFT_RATIO = 0.05              # a process drifts when its thirds differ by more than this and Mann-Whitney rejects at ALPHA
DRIFT_SHARE = 0.2               # a case is flagged when more than this share of its processes drift
NO_VALUE = "-"


def _samples(per_process, metric):
    return [list(runs) for runs in (((c.get("metrics") or {}).get(metric) or {}).get("runs") for c in per_process) if runs]


def _median(values):
    return statistics.median(values) if values else None


def case_row(case_id, samples, metric):
    """One case's metric over its processes: each process contributes the median of its own samples."""
    values = [statistics.median(s) for s in samples]
    ordered, n = sorted(values), len(values)
    low, high, coverage = median_ranks(n)
    shapiro = inference.shapiro_wilk(values)
    within = [s for s in samples if len(s) >= MIN_WITHIN_NORMALITY]
    qq = inference.qq_test(values)
    within_qq = [q for q in map(inference.qq_test, within) if q]
    within_shapiro = [t for t in map(inference.shapiro_wilk, within) if t]
    drifts = [d for d in map(inference.drift, samples) if d]
    tested = [d for d in drifts if d[1] is not None]
    drifting = [d for d in tested if d[1] < inference.ALPHA and abs(d[0] - 1) > DRIFT_RATIO]
    return {
        "case": case_id, "metric": metric, "unit": METRICS[metric], "n": n, "median": statistics.median(values),
        "ciLow": ordered[low - 1], "ciHigh": ordered[high - 1], "ranks": [low, high], "coverage": coverage,
        "cov": descriptive.summarize(values)["cov"],
        "withinCov": _median([descriptive.summarize(s)["cov"] for s in samples if len(s) > 1]),
        "shapiroW": shapiro and shapiro[0], "shapiroP": shapiro and shapiro[1],
        "normal": None if shapiro is None else shapiro[1] >= inference.ALPHA, "qq": qq and qq[0], "qqCritical": qq and qq[1], "qqPass": qq and qq[2],
        "withinQq": _median([q[0] for q in within_qq]),
        "withinQqFail": sum(not q[2] for q in within_qq) / len(within_qq) if within_qq else None,
        "withinNonNormal": sum(p < inference.ALPHA for _, p in within_shapiro) / len(within_shapiro) if within_shapiro else None,
        "driftChecked": len(tested), "drifting": len(drifting), "driftRatio": _median([d[0] for d in drifts]),
        "driftTests": {m: sum(d[2] == m for d in tested) for m in (inference.EXACT, inference.NORMAL_APPROX)},
        "driftFlag": bool(tested) and len(drifting) / len(tested) > DRIFT_SHARE,
    }


def pair_key(case):
    return case["id"].removesuffix(f"_{case.get('variant')}")


def pair_row(key, fixed, not_fixed, metric):
    """notFixed against fixed: each side's per-process medians, never pooled samples."""
    a, b = [statistics.median(s) for s in fixed], [statistics.median(s) for s in not_fixed]
    ratio = inference.ratio_of_medians(a, b)
    test = inference.mann_whitney(a, b)
    delta, magnitude = inference.cliffs_delta(a, b)
    return {
        "pair": key, "metric": metric, "nFixed": len(a), "nNotFixed": len(b),
        "ratio": ratio and ratio[0], "ratioLow": ratio and ratio[1], "ratioHigh": ratio and ratio[2],
        "mannWhitneyU": test and test[0], "mannWhitneyP": test and test[1],
        "mannWhitneyMethod": test and test[2], "cliffsDelta": delta, "magnitude": magnitude,
    }


def build(process_files):
    cases = process_cases(process_files)
    rows, pairs, sides = [], [], {}
    for case_id, per_process in sorted(cases.items()):
        for metric in METRICS:
            samples = _samples(per_process, metric)
            if samples:
                rows.append(case_row(case_id, samples, metric))
        variant = per_process[0].get("variant")
        if variant in (VARIANT_FIXED, VARIANT_NOT_FIXED):
            sides.setdefault(pair_key(per_process[0]), {})[variant] = per_process
    for key, side in sorted(sides.items()):
        if len(side) == 2:
            for metric in METRICS:
                fixed, not_fixed = _samples(side[VARIANT_FIXED], metric), _samples(side[VARIANT_NOT_FIXED], metric)
                if fixed and not_fixed:
                    pairs.append(pair_row(key, fixed, not_fixed, metric))
    return cases, rows, pairs


def _n(x):
    return number(x, NO_VALUE)


def _p(x):
    return NO_VALUE if x is None else f"{x:.3g}"


def _r(x):
    return NO_VALUE if x is None else f"{x:.4f}"


def _share(x):
    return NO_VALUE if x is None else f"{x:.0%}"


def _qq(r):
    if r["qq"] is None:
        return f"n < {inference.QQ_MIN}: not meaningful | {NO_VALUE} | {NO_VALUE}" if r["n"] < inference.QQ_MIN else f"{NO_VALUE} | {NO_VALUE} | {NO_VALUE}"
    return f"{r['qq']:.4f} | {r['qqCritical']:.4f} | {'pass' if r['qqPass'] else 'fail'}"


def _pct(x):
    return NO_VALUE if x is None else f"{x:.1%}"


def markdown(rows, pairs):
    lines = [f"One value per process per case (its median sample; energy is one J/op per process). Bootstrap: seed {inference.BOOTSTRAP_SEED}, "
             f"{inference.BOOTSTRAP_RESAMPLES} resamples of processes. Normal at alpha {inference.ALPHA}. "
             f"QQ r is the probability-plot correlation; its 5% critical value for each n is the 5% quantile of r over {inference.QQ_CRITICAL_DRAWS} seeded normal samples.", "",
             "## Across processes", "",
             "| case | metric | n | median | 95% CI | ranks | coverage | CoV | within CoV (median) | Shapiro-Wilk p | normal | QQ r | QQ 5% critical | QQ |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    lines += [f"| {r['case']} | {r['metric']} ({r['unit']}) | {r['n']} | {_n(r['median'])} | {_n(r['ciLow'])} - {_n(r['ciHigh'])} | "
              f"{r['ranks'][0]}-{r['ranks'][1]} | {r['coverage']:.3f} | {_pct(r['cov'])} | {_pct(r['withinCov'])} | "
              f"{_p(r['shapiroP'])} | {NO_VALUE if r['normal'] is None else 'yes' if r['normal'] else 'no'} | {_qq(r)} |" for r in rows]
    lines += ["", "## Within a process", "",
              f"Drift: median of the last third over the first third of a process's samples; a process drifts above {DRIFT_RATIO:.0%} with Mann-Whitney p < {inference.ALPHA}; "
              f"a case is flagged above {DRIFT_SHARE:.0%} of its processes. Thirds under {inference.DRIFT_MIN_TEST} samples get no p and are not checked. "
              f"Mann-Whitney is exact with no ties and both sides at most {inference.EXACT_MAX}, otherwise normal with continuity correction.", "",
              "| case | metric | QQ r (median) | QQ fails | non-normal processes | processes checked | exact / normal | drifting | last/first (median) | flagged |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    lines += [f"| {r['case']} | {r['metric']} | {_p(r['withinQq'])} | {_share(r['withinQqFail'])} | {_share(r['withinNonNormal'])} | {r['driftChecked']} | "
              f"{r['driftTests'][inference.EXACT]} / {r['driftTests'][inference.NORMAL_APPROX]} | {r['drifting']} | "
              f"{_p(r['driftRatio'])} | {'yes' if r['driftFlag'] else 'no'} |" for r in rows]
    lines += ["", "## notFixed against fixed", "",
              "| pair | metric | n fixed / notFixed | median ratio notFixed/fixed | 95% CI | Mann-Whitney p | method | Cliff's delta | magnitude |",
              "|---|---|---|---|---|---|---|---|---|"]
    lines += [f"| {p['pair']} | {p['metric']} | {p['nFixed']} / {p['nNotFixed']} | {_r(p['ratio'])} | {_r(p['ratioLow'])} - {_r(p['ratioHigh'])} | "
              f"{_p(p['mannWhitneyP'])} | {p['mannWhitneyMethod'] or NO_VALUE} | {p['cliffsDelta']:+.3f} | {p['magnitude']} |" for p in pairs]
    return "\n".join(lines) + "\n"


def write(out, process_files):
    cases, rows, pairs = build(process_files)
    target = paths.Analysis(pathlib.Path(out))
    target.credibility.parent.mkdir(parents=True, exist_ok=True)
    target.credibility.write_text(markdown(rows, pairs))
    target.credibility_data.write_text(json.dumps({"bootstrap": {"seed": inference.BOOTSTRAP_SEED, "resamples": inference.BOOTSTRAP_RESAMPLES},
                                                   "cases": rows, "pairs": pairs}, indent=1) + "\n")
    import chart_draw
    for case_id in cases:
        panels = [(r["metric"], [statistics.median(s) for s in _samples(cases[case_id], r["metric"])], r["qq"], r["qqCritical"])
                  for r in rows if r["case"] == case_id and r["n"] >= inference.QQ_MIN]
        if panels:
            chart_draw.qq_lines(case_id, panels, out)
    return rows, pairs


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: credibility.py <out dir> <benchmark.json of each process>...")
    rows, pairs = write(sys.argv[1], sys.argv[2:])
    flagged = [r for r in rows if r["driftFlag"]]
    print(f"cases={len({r['case'] for r in rows})} pairs={len({p['pair'] for p in pairs})} drifting={len(flagged)}")
    for r in flagged:
        print(f"  drift: {r['case']} {r['metric']}: {r['drifting']} of {r['driftChecked']} processes")


if __name__ == "__main__":
    main()
