"""parity/defaults.yaml, which :config's DefaultsFileTest pins to what Kotlin writes, is where the Python readers take their defaults."""
from cryptobench.shared.settings import defaults, energy_capture


def test_a_key_with_a_default_reads_it_and_one_without_reads_none():
    assert defaults.at("run.metrics") == ["TIME"]
    assert defaults.at("run.launchRetries") == 2
    assert defaults.at("run.orderSeed") is None
    assert defaults.at("run.thermalGate.discardLimit") is None


def test_the_energy_capture_rule_defaults_to_the_written_capture_and_source():
    assert energy_capture.DEFAULT == defaults.at("run.harness.energy") == {"capture": "none", "source": "rails"}
    assert (energy_capture.capture({}), energy_capture.source(None)) == ("none", "rails")
