"""energyJ's kind from benchmark.json to the dossier and the report: estimated is labelled, never compared with measured."""
import json
from dataclasses import replace

from helpers import summary
from site_replace_data import item
from test_dossier import ROWS, build, scope

from perfrepair.data_handler.inbound.results import read_results
from perfrepair.ai.suggest.site_replace.render import render
from perfrepair.dto.measurement import Measurements
from perfrepair.dto.perf_mode import PerfMode
from perfrepair.dto.site import Dossier
from perfrepair.report.markdown import _metric_lines
from perfrepair.report.metrics import metric_rows
from perfrepair.report.summary import _estimated_in
from perfrepair.validation.dossiers import check_dossier
from perfrepair.validation.measurements import validate_measurements
from perfrepair.validation.report import _metric


def benchmark(tmp_path, block):
    path = tmp_path / "benchmark.json"
    metrics = {"timeNs": {"iterations": 1, "runs": [10.0, 11.0]}} | ({"energyJ": block} if block else {})
    path.write_text(json.dumps({"cases": [{"id": "c", "type": "T", "algorithm": "A", "provider": "P", "operation": "OP",
                                           "parameters": {}, "metrics": metrics}]}))
    return path


def test_inbound_carries_the_kind_on_the_energy_metric_only(tmp_path):
    rows, m = read_results(benchmark(tmp_path, {"iterations": 9, "runs": [0.5], "source": "manafa", "kind": "estimated"}))
    assert m["c"]["energyJ"].kind == "estimated" and m["c"]["energyJ"].median == 0.5 and m["c"]["timeNs"].kind is None
    document = Measurements({}, [], m)
    assert document.to_json()["measurements"]["c"]["energyJ"]["kind"] == "estimated"
    assert "kind" not in document.to_json()["measurements"]["c"]["timeNs"]
    assert Measurements.from_json(document.to_json()).byRow["c"]["energyJ"].kind == "estimated"
    assert validate_measurements(document, rows) == []


def test_a_file_without_a_kind_reads_as_rails_and_one_without_energy_has_no_key(tmp_path):
    assert read_results(benchmark(tmp_path, {"iterations": 9, "runs": [0.5]}))[1]["c"]["energyJ"].kind == "measured"
    assert "energyJ" not in read_results(benchmark(tmp_path, None))[1]["c"]


def energy(c, o):
    return {"c64": {"timeNs": summary(100), "energyJ": replace(summary(10), kind=c)},
            "o64": {"timeNs": summary(80), "energyJ": replace(summary(5), kind=o)}}


def only_option(tmp_path, c, o):
    rows = [r for r in ROWS if r.rowId in ("c64", "o64")]
    document = build([scope()], tmp_path, rows=rows, measurements=energy(c, o))
    return document, next(x for x in document["dossiers"][0]["options"] if x["item"] == "TypeA|ALG-A|P2")


def test_two_estimated_sides_give_a_labelled_estimate(tmp_path):
    document, option = only_option(tmp_path, "estimated", "estimated")
    joules = next(e for e in option["estimates"] if e["metric"] == "energyJ")
    assert joules["kind"] == "estimated" and joules["configuration"].endswith(", estimated") and joules["ratio"] == 0.5
    assert "noEstimates" not in option
    assert all("kind" not in e for e in option["estimates"] if e["metric"] == "timeNs")
    text = render(item(Dossier.from_json(document["dossiers"][0])))
    assert "energyJ | 0.500" in text and ", estimated" in text


def test_two_measured_sides_are_unlabelled(tmp_path):
    _, option = only_option(tmp_path, "measured", "measured")
    joules = next(e for e in option["estimates"] if e["metric"] == "energyJ")
    assert joules["kind"] == "measured" and "estimated" not in joules["configuration"]


def test_sides_of_different_kinds_have_no_energy_estimate_and_say_why(tmp_path):
    document, option = only_option(tmp_path, "measured", "estimated")
    assert [e["metric"] for e in option["estimates"]] == ["timeNs"]
    assert [(n["metric"], n["reason"]) for n in option["noEstimates"]] == [("energyJ", "energy_kinds_differ")]
    assert Dossier.from_json(document["dossiers"][0]).to_json() == document["dossiers"][0]
    assert check_dossier(document["dossiers"][0], "app", PerfMode())[1] == []


def case(kind, runs=(0.5, 0.6)):
    block = {"iterations": 1, "runs": list(runs)} | ({"kind": kind} if kind else {})
    return {"inputSize": None, "metrics": {"timeNs": {"runs": [10.0, 11.0]}, "energyJ": block}}


def energy_row(before, after):
    return metric_rows(before, after)[2]


def test_the_report_labels_an_estimate_and_validates_it():
    m = energy_row(case("estimated"), case("estimated"))
    assert m["kind"] == "estimated" and m["measured"] is True and _metric("r", m) == []
    assert "| energyJ (J/op, estimated) |" in _metric_lines(m)[0]


def test_the_report_of_rails_energy_is_what_it_was():
    for kind in ("measured", None):
        m = energy_row(case(kind), case(kind))
        assert "kind" not in m and _metric("r", m) == [] and "| energyJ (J/op) |" in _metric_lines(m)[0]


def test_the_report_refuses_a_ratio_across_kinds():
    m = energy_row(case("measured"), case("estimated"))
    assert m["measured"] is False and m["reason"] == "energy_kinds_differ: measured before, estimated after" and _metric("r", m) == []


def test_the_summary_names_the_apps_with_estimates():
    reports = [{"app": "a", "scopes": [{"metrics": [{"metric": "energyJ", "kind": "estimated"}]}]},
               {"app": "b", "scopes": [{"metrics": [{"metric": "energyJ", "measured": True}]}]}]
    assert _estimated_in(reports, "energyJ") == {"estimatedIn": ["a"]} and _estimated_in(reports, "timeNs") == {}

