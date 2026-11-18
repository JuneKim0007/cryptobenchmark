"""An unreadable temperature before the run-level warm-up skips it; the device is never instrumented for it."""

from cryptobench.stages.measurement.session import warmup


class Unreadable:
    def __init__(self):
        self.held = []

    def hold(self, label):
        self.held.append(label)
        return False


class NoDevice:
    def instrument(self, *_arguments, **_options):
        raise AssertionError("instrumented although the temperature was unreadable")


def test_the_warm_up_is_skipped_when_the_temperature_cannot_be_read(capsys):
    gate = Unreadable()
    document = {"run": {"warmup": {"iterations": 5, "jobs": [], "cases": 3}}}
    assert warmup.run(NoDevice(), "CryptoBenchmark", [], ["a", "b"], [], document, gate, dict) == []
    assert gate.held == ["warm-up"]
    assert "WARM-UP SKIPPED: temperature_unreadable" in capsys.readouterr().out

