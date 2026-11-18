"""SIGTERM and SIGHUP stop a run as Ctrl-C does: the case on the device is force-stopped, then the hooks are abandoned."""
import signal

import pytest

import pipeline
from cryptobench.stages.measurement.session import measure as measure_session
from fake_phone import Phone


@pytest.fixture
def restored():
    before = {stop: signal.getsignal(stop) for stop in pipeline.STOP_SIGNALS}
    yield
    for stop, handler in before.items():
        signal.signal(stop, handler)


@pytest.mark.parametrize("name", ["SIGTERM", "SIGHUP"])
def test_a_stop_signal_during_a_case_force_stops_the_device_like_ctrl_c(tmp_path, monkeypatch, restored, name):
    if not hasattr(signal, name):
        pytest.skip(f"{name}: not on this platform")
    pipeline.stop_like_ctrl_c()
    phone = Phone(tmp_path, cases=("a", "b"))
    measured = phone.instrument

    def signalled(test_class, *arguments, step="instrument"):
        if "b" in arguments:
            signal.raise_signal(getattr(signal, name))
        return measured(test_class, *arguments, step=step)
    monkeypatch.setattr(phone, "instrument", signalled)
    with pytest.raises(KeyboardInterrupt):
        measure_session.run_session(phone, measure_session.Plan("CryptoBenchmark", ()), 1, [], lambda _repetition: tmp_path / "benchmark", [])
    assert phone.log[-1] == "force-stop"
    assert (tmp_path / "benchmark/cases/a.json").is_file()


def test_main_maps_the_stop_signals_before_reading_its_options(monkeypatch, restored):
    for stop in pipeline.STOP_SIGNALS:
        signal.signal(stop, signal.SIG_DFL)

    def options():
        raise SystemExit(0)
    monkeypatch.setattr(pipeline, "parse_options", options)
    with pytest.raises(SystemExit):
        pipeline.main()
    assert pipeline.STOP_SIGNALS and all(signal.getsignal(stop) is signal.default_int_handler for stop in pipeline.STOP_SIGNALS)
