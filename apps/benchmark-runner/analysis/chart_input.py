"""What a chart run reads: the measured cases, which chart group each belongs to, and the analysis settings."""
import json
import pathlib


from cryptobench.shared.stats.units import DisplayUnits
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.settings.effective_view import AnalysisView, found
# ChartGroup ids and labels in :preparation; names_check holds each equal to it
UNIDENTIFIED = (0, "unidentified")
SYMMETRIC_CIPHER, ASYMMETRIC_CIPHER, SIGNATURE = (1, "symmetric-cipher"), (2, "asymmetric-cipher"), (3, "signature")
HASH, MAC, KEYGEN_SYMMETRIC, KEYGEN_ASYMMETRIC = (4, "hash"), (5, "mac"), (8, "keygen-symmetric"), (9, "keygen-asymmetric")


def _yaml(path):
    return (read_yaml(path)) if pathlib.Path(path).is_file() else {}


def load(benchmark_file, prepared_file, effective_file):
    cases = json.load(open(benchmark_file))["cases"]
    groups = {c["id"]: (c.get("chartGroupId", UNIDENTIFIED[0]), c.get("chartGroup", UNIDENTIFIED[1])) for c in _yaml(prepared_file).get("cases", [])}
    return cases, groups, _yaml(effective_file)


def process_cases(process_files):
    """Each case id with its case from every process file, in file order; a merged file loses which process ran what."""
    cases = {}
    for file in process_files:
        for case in json.loads(pathlib.Path(file).read_text())["cases"]:
            cases.setdefault(case["id"], []).append(case)
    return cases


def settings(effective):
    view = AnalysisView(effective)
    return {
        "charts": view.charts,
        "dir": view.dir,
        "headline": view.headline,
        "limit": float(view.limit),
        "run_id": effective.get("runId") or "adhoc",
        "units": DisplayUnits.parse({**AnalysisView({}).units, **view.units}, "analysis.units"),
        # count-metric bars (allocationCount) are drawn unless an explicit analysis.charts list leaves "countBars" out
        "countBars": found(effective, "analysis.charts") is None or "countBars" in (view.charts or []),
    }
