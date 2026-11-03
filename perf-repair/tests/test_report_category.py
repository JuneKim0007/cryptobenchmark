"""The two categories in the report: each row's pattern, the summary split by it, and category_mismatch."""
import pytest
from helpers import LATENCY, QUIET
from test_app_report import A, B, make_app

from perfrepair.config.load import load
from perfrepair.config.stops import install_stops
from perfrepair.files import read_json, write_json
from perfrepair.report.command import app_report, device_summary
from perfrepair.result.category import category_mismatch
from perfrepair.run_dir import AppPaths
from perfrepair.stop import Halt
from perfrepair.validation.report import validate_report, validate_summary


def _m(change, selected=True, measured=True):
    return {"metric": "timeNs", "selected": selected, "measured": measured, "change": change}


def _e(ratio, p):
    return {"metric": "timeNs", "ratio": ratio, "pImprove": p}


@pytest.mark.parametrize("metric, estimates, found", [
    (_m("worse"), [_e(0.7, 0.99)], ["timeNs"]),
    (_m("improved"), [_e(1.5, 0.01)], ["timeNs"]),
    (_m("improved"), [_e(0.7, 0.99)], []),
    # a function doing more than the primitive dilutes the ratio: unchanged never contradicts
    (_m("unchanged"), [_e(0.7, 0.99)], []),
    (_m("worse", selected=False), [_e(0.7, 0.99)], []),
    (_m("worse"), [], []),
    (_m("improved"), [_e(0.95, 0.6)], ["timeNs"]),
])
def test_the_mismatch_rule(metric, estimates, found):
    assert category_mismatch([metric], estimates) == found


def _fixed_a(run):
    paths = AppPaths(run, "shop")
    doc = read_json(paths.scopes)
    for s in doc["scopes"]:
        if s["id"] == A:
            s.update(pattern="fixed", patternReason="held_in_field")
    write_json(paths.scopes, doc)


def test_rows_carry_the_pattern_and_the_summary_never_mixes_the_two(tmp_path):
    make_app(tmp_path)
    _fixed_a(tmp_path)
    make_app(tmp_path, "slow", after_scale=1.5)
    reports = [app_report(tmp_path, n, LATENCY, **QUIET) for n in ("shop", "slow")]
    rows = {r["scope"]: r for r in reports[0]["scopes"]}
    assert (rows[A]["pattern"], rows[A]["patternReason"]) == ("fixed", "held_in_field")
    assert (rows[B]["pattern"], rows[B]["patternReason"]) == ("notFixed", "unknown_default")
    doc = device_summary(tmp_path, **QUIET)
    assert doc["metrics"]["fixed"]["timeNs"]["ratios"] == {"shop": pytest.approx(0.8), "slow": None}
    assert doc["metrics"]["notFixed"]["timeNs"]["ratios"]["shop"] is None
    assert [(s["pattern"], s["apps"]) for s in doc["swaps"]] == [("fixed", ["shop"]), ("notFixed", ["shop", "slow"])]
    assert doc["patterns"]["byApp"]["shop"] == {"fixed": 1, "notFixed": 4, "unknownDefault": 4, "categoryMismatch": 0}
    assert doc["patterns"]["all"]["unknownDefault"] == 9
    assert validate_summary(doc, reports) == []
    text = (tmp_path / "summary.md").read_text()
    assert "## Category fixed" in text and "## Category notFixed" in text and "| shop | 1 | 4 | 4 | 0 |" in text


def test_a_before_after_against_the_estimate_warns_and_a_stop_setting_stops(tmp_path):
    make_app(tmp_path, after_scale=1.5)
    doc = app_report(tmp_path, "shop", LATENCY, **QUIET)
    row = next(r for r in doc["scopes"] if r["scope"] == A)
    assert row["categoryMismatch"] == ["timeNs"] and validate_report(doc, "shop") == []
    assert "category_mismatch on timeNs" in AppPaths(tmp_path, "shop").report_md.read_text()
    bad = {**doc, "scopes": [{**r, "categoryMismatch": []} for r in doc["scopes"]]}
    assert any("categoryMismatch" in p for p in validate_report(bad, "shop"))
    settings = tmp_path / "perfrepair.yaml"
    settings.write_text("stops: {category_mismatch: stop}\n")
    install_stops(load(settings, {}, {}))
    with pytest.raises(Halt, match="category_mismatch"):
        app_report(tmp_path, "shop", LATENCY, **QUIET)
