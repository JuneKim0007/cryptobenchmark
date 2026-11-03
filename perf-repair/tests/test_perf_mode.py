import pytest

from perfrepair.dto.metrics import ALLOCATIONS, ENERGY, METRICS, TIME
from perfrepair.dto.perf_mode import GENERIC, KEYS, PerfMode


def test_generic_selects_every_registry_metric_and_requires_none():
    g = PerfMode.parse(GENERIC)
    assert g.generic and g.metrics == METRICS and g.required == () and g.to_json() == GENERIC
    assert g.views(TIME) == ("latency", "throughput")


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
