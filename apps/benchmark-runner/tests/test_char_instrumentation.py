"""Characterization (Py-P3): each instrumentation site's device calls in order against golden/instrumentation_*.txt (UPDATE_GOLDEN=1 rewrites them),
a transport lost mid-step on the probe, check, interop and harness routes, and the probe's pass rule."""
import os, pathlib, re, types

import pytest

import test_device_benchmark_flow as flow
from cryptobench.shared import paths
from cryptobench.shared.device.adb import DeviceError, DeviceLost
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


def normalised(calls, tmp_path):
    text = "".join(f"{c}\n" for c in calls).replace(str(tmp_path), "<tmp>")
    return re.sub(r"hostMillis \d+", "hostMillis <ms>", text)


def matches(name, calls, tmp_path):
    golden = GOLDEN / f"instrumentation_{name}.txt"
    text = normalised(calls, tmp_path)
    if os.environ.get("UPDATE_GOLDEN"):
        golden.write_text(text)
    assert text == golden.read_text()


OPTIONS = types.SimpleNamespace(suppress_errors="")


def site_probe(phone, tmp_path):
    probe(phone, tmp_path / "discovery", ("-e", "bundled", "x"))


def site_check(phone, tmp_path):
    check.on_device(phone, OPTIONS, tmp_path / "effective.yaml", tmp_path / "probe.yaml", tmp_path / "trial.yaml", tmp_path / "known.yaml", tmp_path / "check")


def site_interop(phone, tmp_path):
    interop_oracle.on_device(phone, tmp_path / "effective.yaml", tmp_path / "probe.yaml", tmp_path / "trial.yaml", tmp_path / "plan.yaml", tmp_path / "out.yaml")


def site_harness(phone, tmp_path):
    harness.scoped_interop(phone, tmp_path / "scoped")


def site_energy_dry(phone, tmp_path):
    EnergySession(phone).dry_pass(tmp_path / "config.txt", tmp_path / "dry.perfetto-trace", tmp_path / "calls.json", tmp_path / "preparation")


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
def test_today_a_transport_lost_mid_step_ends_the_step_though_the_device_is_back(name, tmp_path):
    phone = Recording(tmp_path, lose=1, cases=("a",))
    with pytest.raises(DeviceLost, match=LOST):
        SITES[name](phone, tmp_path)
    assert len([c for c in phone.calls if c.startswith("instrument")]) == 1 and phone.lose == 0
    assert not [c for c in phone.calls[phone.calls.index(next(c for c in phone.calls if c.startswith("instrument"))):] if c.startswith("pull")]


@pytest.mark.parametrize("route", [{"check": True}, {"interop": "plan"}])
def test_today_a_lost_transport_ends_the_check_and_interop_routes_and_publishes_nothing(route, tmp_path, monkeypatch):
    rerun = routed(tmp_path, monkeypatch)
    rerun.phone = Recording(tmp_path, lose=1)
    rerun.phone.connect = lambda: None
    monkeypatch.setattr("pipeline.Device", lambda *_arguments: rerun.phone)
    flags = {"interop": str(rerun.plan)} if "interop" in route else route
    with pytest.raises(DeviceLost, match=LOST):
        rerun(**flags)
    assert [p.name for p in rerun.root.iterdir()] == [paths.LOCK]
    assert [c.split()[1] for c in rerun.phone.calls if c.startswith("instrument")] == ["EndToEndCheck" if "check" in route else "InteropCheck"]


@pytest.mark.parametrize("output", ["Tests run: 1,  Failures: 1\nnot OK (1 test) here\n", "INSTRUMENTATION_STATUS: stack=x OK (1 test)\n"])
def test_today_probe_pass_rule_is_a_substring(output, tmp_path):
    phone = Recording(tmp_path)
    phone.instrument = lambda *_arguments, **_keywords: output
    probe(phone, tmp_path / "discovery")
    assert phone.calls[-1] == f"pull /plan/. {tmp_path / 'discovery'}"


@pytest.mark.parametrize("output", ["OK (2 tests)\n", "OK (1 tests)\n"])
def test_today_probe_refuses_any_other_ok_line(output, tmp_path):
    phone = Recording(tmp_path)
    phone.instrument = lambda *_arguments, **_keywords: output
    with pytest.raises(DeviceError, match="^DeviceProbe failed on the device"):
        probe(phone, tmp_path / "discovery")


def test_today_interop_pushes_its_plan_without_an_aot_compile(tmp_path):
    phone = Recording(tmp_path, cases=("a",))
    site_interop(phone, tmp_path)
    assert not [c for c in phone.calls if "cmd package compile" in c]
    phone = Recording(tmp_path, cases=("a",))
    site_check(phone, tmp_path)
    assert len([c for c in phone.calls if "cmd package compile" in c]) == 2
