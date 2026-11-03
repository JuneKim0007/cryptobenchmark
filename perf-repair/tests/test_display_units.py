from pathlib import Path

import pytest
import yaml

from perfrepair.dto.units import DisplayUnits, number

EXAMPLE = Path(__file__).resolve().parents[2] / "modules/config/example/config_effective_example.yaml"


def test_the_defaults_mirror_what_the_config_module_writes():
    if not EXAMPLE.is_file():
        pytest.skip("perf-repair outside its cryptobenchmark checkout")
    assert DisplayUnits().to_json() == yaml.safe_load(EXAMPLE.read_text())["analysis"]["units"]


def test_a_manifest_without_units_reads_the_defaults_and_a_bad_unit_is_refused():
    assert DisplayUnits.parse(None) == DisplayUnits("ms", "MB/s")
    for bad in ({"latency": "s"}, {"throughput": "GB/s"}, {"time": "ms"}, "ms"):
        with pytest.raises(ValueError, match="invalid: manifest units"):
            DisplayUnits.parse(bad)


def test_a_sub_millisecond_time_keeps_its_significant_figures_and_mb_needs_an_input_size():
    units = DisplayUnits()
    assert number(units.latency_of(662)) == "0.000662" and number(units.latency_of(2_500_000)) == "2.5"
    assert units.throughput_of(1000, None) is None and units.throughput_of(1000, 1024) == 1024.0
    assert DisplayUnits("ns", "ops/s").throughput_of(1000, None) == 1e6
    assert DisplayUnits("ns", "MiB/s").throughput_of(1000, 2 ** 20) == 1e6
