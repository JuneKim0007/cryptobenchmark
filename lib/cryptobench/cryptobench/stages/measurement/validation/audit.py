"""pipeline.py --audit: a campaign's results read, never changed: per unit, pass and case the runs present, relaunches, rejected attempts,
findings and the runs whose median sits outside the case's spread across runs (flagged only), into <results>/audit.yaml."""
import collections, pathlib, statistics

from cryptobench.shared import paths
from cryptobench.shared.document.document import DocumentKind, read_yaml
from cryptobench.shared.document.dump import dump_yaml
from cryptobench.shared.document.write import write_text
from cryptobench.shared.stats.descriptive import summarize
from cryptobench.stages.measurement import resume
from cryptobench.stages.measurement.session import blocks
from cryptobench.stages.measurement.validation import expectation, rules

AUDIT_DOC = DocumentKind("audit", 1)
# Tukey's fences over the runs' medians; fewer runs give no spread to stand outside of
FENCE, SPREAD_RUNS = 1.5, 4
ASIDE = {paths.SUPERSEDED, paths.REJECTED}


def units(root):
    """Every measured unit under root: a folder holding manifest.yaml and benchmark/, outside superseded/ and rejected/."""
    return [manifest.parent for manifest in sorted(root.rglob(paths.MANIFEST))
            if not ASIDE.intersection(manifest.relative_to(root).parts) and paths.RunTree(manifest.parent).benchmark.root.is_dir()]


def rejected(unit):
    """(pass, case) -> rejected attempts, from rejected/*/**/why.yaml."""
    counted = collections.Counter()
    for why in sorted(paths.RunTree(unit).rejected.rglob(paths.WHY)):
        document = read_yaml(why)
        run = pathlib.PurePosixPath(document["run"])
        counted[(run.parent.name or None, document["case"])] += 1
    return counted


def outliers(medians):
    """{run: median} -> the runs outside the fences, when there are enough runs to have a spread."""
    if len(medians) < SPREAD_RUNS:
        return []
    summary = summarize(list(medians.values()))
    low, high = summary["q1"] - FENCE * summary["iqr"], summary["q3"] + FENCE * summary["iqr"]
    return sorted(run for run, median in medians.items() if not low <= median <= high)


def audited_pass(unit, folder, records, attempts):
    """One pass of one unit: per case what its kept runs hold."""
    cases = collections.defaultdict(lambda: {"runsPresent": 0, "relaunched": 0, "rejected": 0, "findings": collections.Counter(), "medians": {}})
    label, runs = records[0]["pass"], 0
    for record in records:
        want = expectation.of(record["identity"]["run"], record["pass"])
        for entry in record["processes"]:
            runs += 1
            run = rules.RunFolder(unit, folder / entry["folder"], folder, entry["repetition"], tuple(entry["problems"]), entry["files"])
            for finding in rules.check_run(run, want):
                if finding.case:
                    cases[finding.case]["findings"][finding.code] += 1
            for case in run.order or ():
                result = run.result(case)
                if result.path.is_file():
                    cases[case]["runsPresent"] += 1
                    if not isinstance(result.benchmarks, str):
                        cases[case]["medians"][run.run] = statistics.median(result.benchmarks[0]["metrics"]["timeNs"]["runs"])
            for relaunch in entry.get("relaunched") or []:
                cases[relaunch["case"]]["relaunched"] += 1
    for (name, case), count in attempts.items():
        if name == label:
            cases[case]["rejected"] += count
    return {"runs": runs, "cases": {case: {"runsPresent": found["runsPresent"], "relaunched": found["relaunched"], "rejected": found["rejected"],
                                           "findings": dict(sorted(found["findings"].items())), "outliers": outliers(found["medians"])}
                                    for case, found in sorted(cases.items())}}


def audit(root):
    """The audit document of every unit under root; reads only."""
    document = {"schemaVersion": AUDIT_DOC.version, "units": {}}
    for unit in units(root):
        by_pass = collections.defaultdict(list)
        for folder, _path, record in resume.records(unit):
            if isinstance(record, dict) and blocks.RECORD_DOC.accepts(record.get("schemaVersion")):
                by_pass[folder].append(record)
        attempts = rejected(unit)
        document["units"][unit.relative_to(root).as_posix() or "."] = {
            (records[0]["pass"] or "single"): audited_pass(unit, folder, records, attempts) for folder, records in by_pass.items()}
    return document


def written(root):
    """audit.yaml at root, the only file the audit writes."""
    root = pathlib.Path(root)
    return write_text(root / paths.AUDIT, dump_yaml(audit(root)))
