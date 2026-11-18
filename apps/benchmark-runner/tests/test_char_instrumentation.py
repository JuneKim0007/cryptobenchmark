"""Characterization (Py-P3): each instrumentation site's device calls in order against golden/instrumentation_*.txt (UPDATE_GOLDEN=1 rewrites them),
a transport lost mid-step on the probe, check, interop, harness and energy dry pass waited out, and the probe's pass rule."""
import os, pathlib, re, types

import pytest

import test_device_benchmark_flow as flow
from cryptobench.shared import paths
from cryptobench.shared.device.adb import DeviceError, DeviceLost
from cryptobench.shared.device.reconnect import Reconnect
from cryptobench.stages.discovery.probe import probe
from cryptobench.stages.measurement.energy.session import EnergySession
from cryptobench.stages.verification import check, harness, interop_oracle
from test_char_publish_routes import RoutePhone, routed

GOLDEN = pathlib.Path(__file__).with_name("golden")
RECORDED = ("run", "shell", "instrument", "pull", "pull_optional", "push_files", "force_stop")
LOST = "device_lost: adb shell am instrument: error: closed"


class Recording(RoutePhone):
    """Every outermost device call with its arguments; a lost transport on the first `lose` instrument calls."""

    def __init__(self, folder, lose=0, **options):
        super().__init__(folder, **options)
        self.calls, self.depth, self.lose = [], 0, lose

    def recorded(name):
        def call(self, *arguments, **keywords):
            if self.depth == 0:
                self.calls.append(" ".join([name, *map(str, arguments)]))
            self.depth += 1
            try:
                if name == "instrument" and self.lose:
                    self.lose -= 1
                    raise DeviceLost(LOST)
                if name == "shell" and "perfetto" in arguments[0] and "--background-wait" in arguments[0]:
                    return "4242\n"
                return getattr(RoutePhone, name)(self, *arguments, **keywords)
            finally:
                self.depth -= 1
        return call

    for _name in RECORDED:
        locals()[_name] = recorded(_name)
    del _name

    def state(self):
        return "device"


def normalised(calls, tmp_path):
    text = "".join(f"{c}\n" for c in calls).replace(str(tmp_path), "<tmp>")
    return re.sub(r"hostMillis \d+", "hostMillis <ms>", text)


def matches(name, calls, tmp_path):
    golden = GOLDEN / f"instrumentation_{name}.txt"
    text = normalised(calls, tmp_path)
    if os.environ.get("UPDATE_GOLDEN"):
        golden.write_text(text)
    assert text == golden.read_text()


OPTIONS = types.SimpleNamespace(suppress_errors="", reconnect_wait_minutes=1, reconnect_poll_seconds=0)


def site_probe(phone, tmp_path):
    probe(phone, tmp_path / "discovery", Reconnect.of(phone, OPTIONS), ("-e", "bundled", "x"))


def site_check(phone, tmp_path):
    check.on_device(phone, OPTIONS, tmp_path / "effective.yaml", tmp_path / "probe.yaml", tmp_path / "trial.yaml", tmp_path / "known.yaml", tmp_path / "check")


def site_interop(phone, tmp_path):
    interop_oracle.on_device(phone, Reconnect.of(phone, OPTIONS), tmp_path / "effective.yaml", tmp_path / "probe.yaml", tmp_path / "trial.yaml", tmp_path / "plan.yaml", tmp_path / "out.yaml")


def site_harness(phone, tmp_path):
    harness.scoped_interop(phone, Reconnect.of(phone, OPTIONS), tmp_path / "scoped")


def site_energy_dry(phone, tmp_path):
    EnergySession(phone, Reconnect.of(phone, OPTIONS)).dry_pass(tmp_path / "config.txt", tmp_path / "dry.perfetto-trace", tmp_path / "calls.json", tmp_path / "preparation")


SITES = {f.__name__[5:]: f for f in (site_probe, site_check, site_interop, site_harness, site_energy_dry)}


@pytest.mark.parametrize("name", SITES)
def test_today_device_calls_of_one_site(name, tmp_path):
    phone = Recording(tmp_path, cases=("a",))
    SITES[name](phone, tmp_path)
    matches(name, phone.calls, tmp_path)


FLOWS = {
    "measure_isolation_case_with_warmup": {"warmup": {"iterations": 5, "jobs": [], "cases": 3}},
}


@pytest.mark.parametrize("name", FLOWS)
def test_today_device_calls_of_a_measuring_session(name, tmp_path, monkeypatch):
    phone = Recording(tmp_path)
    flow.measured(tmp_path, monkeypatch, FLOWS[name], phone=phone)
    matches(name, phone.calls, tmp_path)


@pytest.mark.parametrize("name", SITES)
def test_a_transport_lost_mid_step_is_waited_out_and_the_whole_step_runs_again(name, tmp_path, capsys):
    phone = Recording(tmp_path, lose=1, cases=("a",))
    SITES[name](phone, tmp_path)
    instrumented = [n for n, c in enumerate(phone.calls) if c.startswith("instrument")]
    assert len(instrumented) == 2 and phone.lose == 0
    lost, again = phone.calls[:instrumented[0] + 1], phone.calls[instrumented[0] + 1:]
    # the clears ran again before the second attempt; nothing was pulled from the lost one
    assert not [c for c in lost[lost.index(next(c for c in lost if c.startswith("instrument"))):] if c.startswith("pull")]
    assert [c for c in again if c.startswith("shell rm")] == [c for c in lost if c.startswith("shell rm")]
    assert "device:    back after" in capsys.readouterr().out


@pytest.mark.parametrize("route", [{"check": True}, {"interop": "plan"}])
def test_a_lost_transport_is_waited_out_on_the_check_and_interop_routes(route, tmp_path, monkeypatch):
    rerun = routed(tmp_path, monkeypatch)
    rerun.phone = Recording(tmp_path, lose=1)
    rerun.phone.connect = lambda: None
    monkeypatch.setattr("pipeline.Device", lambda *_arguments: rerun.phone)
    flags = {"interop": str(rerun.plan)} if "interop" in route else route
    rerun(**flags)
    assert paths.RunTree(rerun.device).manifest.is_file()
    assert [c.split()[1] for c in rerun.phone.calls if c.startswith("instrument")][-2:] == ["EndToEndCheck" if "check" in route else "InteropCheck"] * 2


@pytest.mark.parametrize("output", ["Tests run: 1,  Failures: 1\nnot OK (1 test) here\n", "INSTRUMENTATION_STATUS: stack=x OK (1 test)\n",
                                    "OK (2 tests)\n", "OK (1 tests)\n"])
def test_probe_passes_only_on_an_ok_1_test_line(output, tmp_path):
    phone = Recording(tmp_path)
    phone.instrument = lambda *_arguments, **_keywords: output
    with pytest.raises(DeviceError, match="^DeviceProbe failed on the device"):
        site_probe(phone, tmp_path)


def test_interop_pushes_its_plan_with_the_aot_compile_as_check_does(tmp_path):
    for site in (site_interop, site_check):
        phone = Recording(tmp_path, cases=("a",))
        site(phone, tmp_path)
        assert len([c for c in phone.calls if "cmd package compile" in c]) == 2
