"""Stage: report.json and report.md of one app, summary.json and summary.md across a run's apps, validated
before writing."""
from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..files import read_json, write_json, write_text
from ..result.modes import Mode
from ..validation import require
from ..validation.report import validate_report, validate_summary
from .app_report import build_report
from .markdown import report_markdown, summary_markdown
from .summary import build_summary


def app_report(run: Path, app: str, mode: Mode, echo=print) -> dict:
    paths = rd.AppPaths(run, app)
    doc = build_report(paths, mode)
    require(rd.REPORT, validate_report(doc, app))
    write_json(paths.report, doc)
    write_text(paths.report_md, report_markdown(doc))
    f = doc["funnel"]
    echo(f"{paths.report}: {f['scopes']} scopes, {f['replace']} replace, {f['applied']} applied, "
         f"{f['compiled']} compiled, {f['measured']} measured")
    return doc


def run_summary(run: Path, echo=print) -> dict:
    reports = [read_json(d / rd.REPORT) for d in rd.app_dirs(run) if (d / rd.REPORT).is_file()]
    doc = build_summary(reports)
    require(rd.SUMMARY, validate_summary(doc, reports))
    root = Path(run) / rd.APPS
    write_json(root / rd.SUMMARY, doc)
    write_text(root / rd.SUMMARY_MD, summary_markdown(doc))
    echo(f"{root / rd.SUMMARY}: {len(doc['apps'])} apps, {doc['funnel']['measured']} scopes measured")
    return doc
