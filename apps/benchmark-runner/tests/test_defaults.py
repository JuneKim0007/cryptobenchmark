"""contracts/defaults/defaults.yaml, which :config's DefaultsFileTest pins to what Kotlin writes, is where the Python readers take their defaults."""
from cryptobench.shared.settings import defaults, energy_capture


def test_a_key_with_a_default_reads_it_and_one_without_reads_none():
    assert defaults.at("run.metrics") == ["TIME"]
    assert defaults.at("run.launchRetries") == 2
    assert defaults.at("run.energyIdleSeconds") == 120
    assert defaults.at("run.orderSeed") is None
    assert defaults.at("run.thermalGate.discardLimit") == 5
    assert defaults.at("run.thermalGate.temperatureKeptCelsius") is None


def test_the_energy_capture_rule_defaults_to_the_written_capture_and_source():
    # the rule's copy the --energy-python scripts import cannot reach the library, so its defaults are pinned here, not read
    written = defaults.at("run.harness.energy")
    assert {"capture": energy_capture.capture({}), "source": energy_capture.source(None)} == {key: written[key] for key in ("capture", "source")}
