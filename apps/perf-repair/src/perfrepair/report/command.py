"""Stage: report.json and report.md of one app, summary.json and summary.md across a device's apps, validated
before writing."""
from __future__ import annotations

from pathlib import Path

from cryptobench.paths import AppTree, RunTree
from cryptobench.paths import APP_REPORT, SUMMARY
from ..files import read_json, write_json, write_text
from ..log import step
from ..result.modes import Mode
from ..validation import require
from ..validation.report import validate_report
from ..validation.summary import validate_summary
from .app_report import build_report
from .markdown import report_markdown, summary_markdown
from .summary import build_summary


def app_report(device: Path, app: str, mode: Mode, echo=print) -> dict:
    paths = AppTree(device, app)
    with step("report", "app", app=app) as s:
        doc = build_report(paths, mode)
        require(APP_REPORT, validate_report(doc, app))
        write_json(paths.report, doc)
        write_text(paths.report_md, report_markdown(doc))
        s.count(**doc["funnel"])
        s.wrote(paths.report, paths.report_md)
    f = doc["funnel"]
    echo(f"{paths.report}: {f['scopes']} scopes in {f['units']} units, {f['replace']} replace in {f['unitsReplace']} units, {f['applied']} applied, "
         f"{f['compiled']} compiled, {f['interopPassed']} interop passed")
    return doc


def device_summary(device: Path, echo=print) -> dict:
    reports = [read_json(AppTree.at(d).report) for d in RunTree(device).apps() if (AppTree.at(d).report).is_file()]
    device = Path(device)
    with step("report", "summary") as s:
        doc = build_summary(reports)
        require(SUMMARY, validate_summary(doc, reports))
        write_json(RunTree(device).summary, doc)
        write_text(RunTree(device).summary_md, summary_markdown(doc))
        s.count(apps=len(doc["apps"]), interopPassed=doc["funnel"]["interopPassed"])
        s.wrote(RunTree(device).summary, RunTree(device).summary_md)
    echo(f"{RunTree(device).summary}: {len(doc['apps'])} apps, {doc['funnel']['interopPassed']} scopes interop passed")
    return doc
