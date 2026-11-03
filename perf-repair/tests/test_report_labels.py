"""Item by item on the report's hand-built device result: the label, the project beside the id, the swap view, thermal."""
from helpers import LATENCY, LATENCY_ALLOC, QUIET, TIMING
from test_app_report import A, CURRENT, OPTION, make_app

import pytest

from perfrepair.app.facts.project import project_name
from perfrepair.config.load import load
from perfrepair.config.stops import install_stops
from perfrepair.dto.report import THERMAL_MISMATCH, THERMAL_THROTTLED
from perfrepair.files import read_json, write_json
from perfrepair.report.command import app_report, device_summary
from perfrepair.report.thermal import labels, start_gap, thermal_row
from perfrepair.result.modes import mode_of
from perfrepair.run_dir import AppPaths
from perfrepair.stop import Halt
from perfrepair.validation.report import validate_report, validate_summary


def row(doc, sid=A):
    return next(r for r in doc["scopes"] if r["scope"] == sid)


def test_a_row_carries_every_metrics_change_and_the_overall_label(tmp_path):
    make_app(tmp_path)
    doc = app_report(tmp_path, "shop", LATENCY, **QUIET)
    r = row(doc)
    time = next(m for m in r["metrics"] if m["metric"] == "timeNs")
    assert {"ratio", "pImprove", "n", "noise", "change"} <= set(time)
    assert r["label"] == time["change"].replace("improved", "improves") and validate_report(doc, "shop") == []


def test_a_gain_and_a_loss_on_the_selected_metrics_is_a_trade_off(tmp_path):
    make_app(tmp_path)
    paths = AppPaths(tmp_path, "shop")
    bench = read_json(paths.scoped_benchmark)
    for case in bench["cases"]:
        scale = 2.0 if case["id"].endswith(":after") else 1.0
        case["metrics"]["allocationCount"] = {"iterations": 1, "runs": [10 * scale, 10 * scale + 0.1, 10 * scale + 0.2]}
    write_json(paths.scoped_benchmark, bench)
    doc = app_report(tmp_path, "shop", LATENCY_ALLOC, **QUIET)
    assert row(doc)["label"] == "trade_off" and validate_report(doc, "shop") == []
    assert app_report(tmp_path, "shop", LATENCY, **QUIET) and row(read_json(paths.report))["label"] != "trade_off"


def test_the_summary_counts_labels_apart_and_never_mixes_a_trade_off_with_an_improvement(tmp_path):
    make_app(tmp_path)
    make_app(tmp_path, "slow", after_scale=1.5)
    for name in ("shop", "slow"):
        app_report(tmp_path, name, LATENCY, **QUIET)
    doc = device_summary(tmp_path, **QUIET)
    assert doc["labels"]["worse"] >= 1 and doc["labels"]["tradeOffAccepted"] == 0
    assert sum(doc["labels"].values()) == sum(s["decision"]["decision"] == "replace" for n in ("shop", "slow")
                                              for s in read_json(AppPaths(tmp_path, n).report)["scopes"])
    assert "## Decisions by measured label" in (tmp_path / "summary.md").read_text()


def test_the_swap_view_shows_one_swap_on_every_metric_across_the_apps(tmp_path):
    make_app(tmp_path)
    make_app(tmp_path, "slow", after_scale=1.5)
    for name in ("shop", "slow"):
        app_report(tmp_path, name, LATENCY, **QUIET)
    [swap] = device_summary(tmp_path, **QUIET)["swaps"]
    assert (swap["current"], swap["option"], swap["apps"]) == (CURRENT, OPTION, ["shop", "slow"])
    time = swap["metrics"]["timeNs"]
    assert time["ratios"]["slow"] > time["ratios"]["shop"] and "worse" in time["changes"]
    assert f"{CURRENT} → {OPTION}" in (tmp_path / "summary.md").read_text()


def test_each_app_keeps_its_own_mode_in_one_summary(tmp_path):
    make_app(tmp_path)
    make_app(tmp_path, "slow")
    app_report(tmp_path, "shop", LATENCY, **QUIET)
    app_report(tmp_path, "slow", LATENCY_ALLOC, **QUIET)
    doc = device_summary(tmp_path, **QUIET)
    assert doc["modes"] == {"shop": "latency", "slow": "latency+memAlloc"}
    assert list(doc["metrics"]) == ["timeNs", "allocationCount"]
    assert doc["metrics"]["allocationCount"]["ratios"]["shop"] is None
    reports = [read_json(AppPaths(tmp_path, n).report) for n in ("shop", "slow")]
    assert validate_summary(doc, reports) == []
    assert validate_summary({**doc, "modes": {}}, reports) == ["modes are not each report's own"]


def test_the_report_and_summary_name_the_project_and_source_beside_the_id(tmp_path):
    make_app(tmp_path)
    source = tmp_path / "shop-source"
    source.mkdir()
    (source / "settings.gradle.kts").write_text('rootProject.name = "Shop App"\n')
    doc = app_report(tmp_path, "shop", LATENCY, **QUIET)
    assert (doc["project"], doc["source"]) == ("Shop App", str(source.resolve()))
    assert "Project: Shop App." in AppPaths(tmp_path, "shop").report_md.read_text()
    assert device_summary(tmp_path, **QUIET)["named"]["shop"]["project"] == "Shop App"


def test_a_project_without_settings_or_gone_names_its_folder(tmp_path):
    assert project_name(tmp_path / "gone") == "gone"


def block(start=None, end=None, end_status=0):
    return {"start": start, "end": end, "startStatus": 0, "endStatus": end_status}


def test_a_start_gap_past_the_threshold_is_a_mismatch_on_shared_sensors_only():
    a, b = block({"BIG": 40.0, "skin": 30.0}), block({"BIG": 46.5, "other": 90.0})
    assert start_gap(a, b) == 6.5 and labels(a, b) == [THERMAL_MISMATCH]
    assert labels(a, block({"BIG": 42.0})) == []
    assert start_gap(a, block(None)) is None and labels(block(None), block(None)) == []


def test_a_side_that_ended_throttled_is_labelled_and_a_host_run_has_no_row():
    assert labels(block(), block(end_status=2)) == [THERMAL_THROTTLED]
    assert thermal_row({"id": "b"}, {"id": "a"}) is None and thermal_row(None, None) is None
    kept = thermal_row({"thermal": block({"BIG": 1.0}), "thermalThrottleSleepSeconds": 90}, {"thermal": block({"BIG": 1.0})})
    assert kept["before"]["thermalThrottleSleepSeconds"] == 90 and kept["labels"] == []


def _hot(tmp_path):
    make_app(tmp_path)
    paths = AppPaths(tmp_path, "shop")
    bench = read_json(paths.scoped_benchmark)
    for case in bench["cases"]:
        case["thermal"] = block({"BIG": 60.0 if case["id"].endswith(":after") else 40.0}, end_status=1)
        case["thermalThrottleSleepSeconds"] = 90
    write_json(paths.scoped_benchmark, bench)


def test_the_labels_reach_the_report_and_change_no_verdict(tmp_path):
    make_app(tmp_path)
    plain = app_report(tmp_path, "shop", LATENCY, **QUIET)
    (tmp_path / "again").mkdir()
    _hot(tmp_path / "again")
    doc = app_report(tmp_path / "again", "shop", LATENCY, **QUIET)
    assert row(doc)["thermal"]["labels"] == [THERMAL_MISMATCH, THERMAL_THROTTLED]
    assert row(doc)["verdict"] == row(plain)["verdict"] and row(doc)["label"] == row(plain)["label"]
    assert "thermal_mismatch" in AppPaths(tmp_path / "again", "shop").report_md.read_text()
    assert device_summary(tmp_path / "again", **QUIET)["thermal"] == {THERMAL_MISMATCH: 1, THERMAL_THROTTLED: 1}


def test_stops_turn_the_mismatch_into_a_stop(tmp_path):
    _hot(tmp_path)
    settings = tmp_path / "perfrepair.yaml"
    settings.write_text("stops: {thermal_mismatch: stop}\n")
    install_stops(load(settings, {}, {}))
    with pytest.raises(Halt, match="thermal_mismatch"):
        app_report(tmp_path, "shop", LATENCY, **QUIET)


def test_timing_is_a_plain_list_in_the_report(tmp_path):
    make_app(tmp_path)
    assert app_report(tmp_path, "shop", mode_of(TIMING), **QUIET)["mode"] == "latency+throughput"
