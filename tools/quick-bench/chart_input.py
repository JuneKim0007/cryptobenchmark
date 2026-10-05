"""What a chart run reads: the measured cases, which chart group each belongs to, and the analysis settings."""
import json
import pathlib

import yaml

# Mirrors AnalysisSettings in :config. effective.yaml always carries these, so they apply only when that file is
# missing; test_charts.py compares them with the committed effective example so the two cannot drift apart.
DEFAULTS = {"charts": ["iqrBars", "throughput", "latency", "stability"], "headline": "auto", "meanUpToCovPercent": 5.0}
UNIDENTIFIED = (0, "unidentified")      # ChartGroup.UNIDENTIFIED in :preparation


def _yaml(path):
    return (yaml.safe_load(pathlib.Path(path).read_text()) or {}) if pathlib.Path(path).is_file() else {}


def load(benchmark_file, prepared_file, effective_file):
    cases = json.load(open(benchmark_file))["cases"]
    groups = {c["id"]: (c.get("chartGroupId", UNIDENTIFIED[0]), c.get("chartGroup", UNIDENTIFIED[1])) for c in _yaml(prepared_file).get("cases", [])}
    return cases, groups, _yaml(effective_file)


def settings(effective):
    analysis = effective.get("analysis") or {}
    statistic = analysis.get("statistic") or {}
    return {
        "charts": analysis["charts"] if "charts" in analysis else DEFAULTS["charts"],
        "dir": analysis.get("dir"),
        "headline": statistic.get("headline", DEFAULTS["headline"]),
        "limit": float(statistic.get("meanUpToCovPercent", DEFAULTS["meanUpToCovPercent"])),
        "run_id": effective.get("runId") or "adhoc",
    }
