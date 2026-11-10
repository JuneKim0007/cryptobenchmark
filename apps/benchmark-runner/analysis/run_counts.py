"""run-counts.md: what each case really ran, read from every process's file because the merged one keeps only the first run's calls per iter.

    run_counts.py <out dir> <benchmark.json of each process>...
"""
import json
import pathlib
import sys

from cryptobench import paths

TIME = "timeNs"


def spread(values):
    low, high = min(values), max(values)
    return str(low) if low == high else f"{low}-{high}"


def rows(process_files):
    """(case, runs kept, iters per run, calls per iter, runs discarded for heat, seconds waited for temperature), one per case."""
    cases = {}
    for file in process_files:
        for case in json.loads(pathlib.Path(file).read_text())["cases"]:
            samples = (case.get("metrics") or {}).get(TIME)
            if samples:
                cases.setdefault(case["id"], []).append((samples, case.get("gate") or {}))
    return [(case, len(runs), spread([len(s["runs"]) for s, _ in runs]), spread([s["iterations"] for s, _ in runs]),
             sum(g.get("discards", 0) for _, g in runs), round(sum(g.get("waitedSeconds", 0.0) for _, g in runs), 1))
            for case, runs in sorted(cases.items())]


def write(out, process_files):
    table = rows(process_files)
    lines = ["| case | runs | iters per run | calls per iter | runs discarded for heat | waited for temperature (s) |", "|---|---|---|---|---|---|"]
    lines += ["| " + " | ".join(map(str, row)) + " |" for row in table]
    lines += ["", f"{sum(r[1] for r in table)} runs in all, {sum(r[4] for r in table)} discarded for heat, {sum(r[5] for r in table):.1f} s waited for temperature"]
    target = paths.Analysis(pathlib.Path(out)).run_counts
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n")


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: run_counts.py <out dir> <benchmark.json of each process>...")
    write(sys.argv[1], sys.argv[2:])


if __name__ == "__main__":
    main()
