import pytest

from perfrepair.dto.metrics import ALLOCATIONS, ENERGY, METRICS, TIME
from perfrepair.dto.perf_mode import ALL, GENERIC, KEYS, PerfMode


@pytest.mark.parametrize("spelling", [GENERIC, ALL])
def test_generic_is_the_plain_list_of_every_key_with_only_the_rule_differing(spelling):
    g = PerfMode.parse(spelling)
    listed = PerfMode.parse(list(KEYS))
    assert g.overall and not listed.overall and g.keys == listed.keys == KEYS
    assert g.metrics == listed.metrics == METRICS and g.required == listed.required == METRICS
    assert g.to_json() == GENERIC and PerfMode.parse(g.to_json()) == g and listed.to_json() == list(KEYS)
    assert g.views(TIME) == ("latency", "throughput")


def test_a_future_metric_in_the_registry_joins_every_key():
    assert KEYS == tuple(k for m in METRICS for k in m.selects)


def test_the_union_of_several_apps_is_a_plain_list():
    both = PerfMode.union([PerfMode.parse(["energy"]), PerfMode.parse(["latency"])])
    assert both.keys == ("latency", "energy") and not both.overall


def test_selection_is_the_registry_metrics_whose_selects_match():
    p = PerfMode.parse(["throughput", "energy", "latency"])
    assert p.keys == ("latency", "throughput", "energy") and p.name == "latency+throughput+energy"
    assert p.metrics == (TIME, ENERGY) and ALLOCATIONS not in p.metrics


def test_latency_and_throughput_are_one_metric_shown_as_selected():
    assert PerfMode.parse(["throughput"]).metrics == (TIME,)
    assert PerfMode.parse(["throughput"]).views(TIME) == ("throughput",)
    assert PerfMode.parse(["latency", "throughput"]).metrics == (TIME,)


def test_text_forms_and_names_parse_back():
    assert PerfMode.parse("energy,latency") == PerfMode.parse("latency+energy") == PerfMode(("latency", "energy"))
    assert all(PerfMode.parse(PerfMode((k,)).name).keys == (k,) for k in KEYS)


@pytest.mark.parametrize("bad", ["battery", [], ["latency", "speed"], 3, None])
def test_anything_else_is_refused(bad):
    with pytest.raises(ValueError, match="perfMode"):
        PerfMode.parse(bad)
