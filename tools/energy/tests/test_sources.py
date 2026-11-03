"""The source seam: rails stays what it was; manafa through its real process, with a fake manafa on the path."""
import json, os, pathlib, sys

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import rails_run  # noqa: E402
from sources import SOURCES  # noqa: E402
from sources import rails_source as rails_module  # noqa: E402
from sources.rails_source import RailsSource  # noqa: E402
from sources.runner import EnergyError, Host, case_arguments  # noqa: E402

FAKE = pathlib.Path(__file__).parent / "fake_manafa"
GOLDEN = rails_run.FIXTURES / "rails_energy.json"


def test_rails_preflight_and_energy_write_the_recorded_bytes(tmp_path, monkeypatch):
    rails_run.install_fake_trace(monkeypatch)
    assert rails_run.run_preflight(tmp_path) == (rails_run.FIXTURES / "rails_preflight.yaml").read_text()
    assert rails_run.run_energy(tmp_path) == GOLDEN.read_text()


def test_rails_calls_its_tools_with_the_arguments_it_always_had(tmp_path, monkeypatch):
    calls = []
    sessions = []

    class Recording(Host):
        def tool(self, script, *arguments):
            calls.append((script, *map(str, arguments)))

    class Session:
        def preflight(self, *paths):
            sessions.append(paths)

    monkeypatch.setattr(rails_module.time, "sleep", lambda seconds: calls.append(("sleep", seconds)))
    source = RailsSource(Recording("py"))
    capability = source.preflight(Session(), tmp_path, True)
    folder = tmp_path / "energy-preflight"
    assert capability == tmp_path / "energy.yaml"
    assert sessions == [(folder / "rails.pbtx", folder / "idle.pftrace", folder / "busy.pftrace")]
    assert "battery_poll_ms: 100 collect_power_rails: true" in (folder / "rails.pbtx").read_text()
    assert "duration_ms: 3000" in (folder / "rails.pbtx").read_text()
    assert calls == [("preflight.py", str(folder / "idle.pftrace"), str(folder / "busy.pftrace"), "3", str(capability),
                      "--accept-unresponsive"), ("sleep", 15)]
    calls.clear()
    with source.window(tmp_path):
        pass
    p, t = tmp_path / "p", tmp_path / "t"
    source.joules({"measured", "dry"}, "cap", p, "data", t, "calls", "out")
    assert calls == [("energy.py", "--capability", "cap", "-o", "out", "--prepared", str(p / "prepared.yaml"), "--benchmark-data", "data",
                      "--traces", str(t), "--dry-trace", str(t / "dry.pftrace"), "--dry-calls", "calls")]


def test_scoped_runs_pass_no_dry_calls():
    assert case_arguments({"measured"}, "c", pathlib.Path("s"), "d", pathlib.Path("t"), None, "o")[:4] == ["--capability", "c", "-o", "o"]


def manafa(monkeypatch, behaviour="", on_path=True):
    monkeypatch.setenv("FAKE_MANAFA", behaviour)
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join([str(FAKE)] if on_path else []))
    return SOURCES["manafa"](Host(sys.executable))


def run_window(source, folder):
    rails_run.inputs(folder)
    with source.window(folder):
        pass
    source.joules({"measured", "dry"}, folder / "energy.yaml", folder, folder / "data.json", folder, folder / "calls.yaml",
                  folder / "energy.json")
    return json.loads((folder / "energy.json").read_text())


def test_a_missing_manafa_is_one_coded_line(tmp_path, monkeypatch):
    source = manafa(monkeypatch, on_path=False)
    with pytest.raises(EnergyError) as window:
        source.window(tmp_path).__enter__()
    assert str(window.value).startswith("manafa_missing: ") and "requirements-manafa.txt" in str(window.value) and "\n" not in str(window.value)
    with pytest.raises(EnergyError) as check:
        source.preflight(None, tmp_path, False)
    assert str(check.value).startswith("manafa_missing: ")
    assert yaml.safe_load((tmp_path / "energy.yaml").read_text())["started"] is False


def test_the_check_reports_what_it_got_and_never_reads_rails(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sources.manafa_source.PREFLIGHT_SECONDS", 0)
    capability = manafa(monkeypatch).preflight(None, tmp_path, False)
    document = yaml.safe_load(capability.read_text())
    assert (document["source"], document["kind"], document["started"], document["usable"]) == ("manafa", "estimated", True, True)
    assert document["cpuFrequencyEvents"] == 2 and document["batteryStatsEvents"] == 1 and document["joules"] > 0
    assert "railsPresent" not in document
    assert capsys.readouterr().out.startswith("manafa:    started, 2 cpu frequency events")


@pytest.mark.parametrize("behaviour, reason", [
    ("init=fails", "adb: no devices second line"), ("cover=none", "no_cpu_frequency_events"), ("battery=none", "no_batterystats"),
    ("stop=fails", "manafa_stop_failed: unable to pull trace file"), ("consumption=fails", "consumption_failed: no samples"),
    ("consumption=zero", "no_estimate: 0.0")])
def test_a_check_that_got_no_number_refuses_with_a_code(tmp_path, monkeypatch, behaviour, reason):
    monkeypatch.setattr("sources.manafa_source.PREFLIGHT_SECONDS", 0)
    with pytest.raises(EnergyError) as refused:
        manafa(monkeypatch, behaviour).preflight(None, tmp_path, False)
    assert str(refused.value) == f"manafa_cannot_start: {reason}"


def test_each_case_window_gets_its_own_estimate(tmp_path, monkeypatch):
    document = run_window(manafa(monkeypatch), tmp_path)
    assert (document["source"], document["kind"], document["powerProfile"]) == ("manafa", "estimated", "power_profile_probed.xml")
    assert "railsResponsive" not in document
    m1, d1 = document["cases"]["m1"], document["cases"]["d1"]
    assert m1["valid"] and m1["capture"] == "measured" and m1["operations"] == 120
    assert m1["joulesPerOperation"] == pytest.approx(m1["joules"] / 120)
    assert m1["netJoules"] is None and "rails" not in m1 and "polls" not in m1 and m1["components"] == {"cpu": m1["joules"]}
    assert d1["valid"] and d1["capture"] == "dry" and d1["operations"] == 77
    assert d1["joules"] != m1["joules"]


@pytest.mark.parametrize("behaviour, reason", [
    ("cover=0.000000001", "window_uncovered"), ("battery=none", "no_batterystats"), ("consumption=zero", "no_estimate: 0.0"),
    ("consumption=fails", "consumption_failed: no samples"), ("stop=fails", "manafa_stop_failed: unable to pull trace file")])
def test_a_window_without_a_number_is_not_measured_and_fills_none(tmp_path, monkeypatch, behaviour, reason):
    case = run_window(manafa(monkeypatch, behaviour), tmp_path)["cases"]["m1"]
    assert case["valid"] is False and case["invalid"] == [f"not_measured: {reason}"] and case["notMeasured"] == reason
    assert case["joules"] is None and case["joulesPerOperation"] is None and case["operations"] == 120


def test_a_run_that_fails_inside_the_window_stops_manafa_and_writes_nothing(tmp_path, monkeypatch):
    source = manafa(monkeypatch)
    with pytest.raises(ValueError):
        with source.window(tmp_path):
            raise ValueError("the device run failed")
    assert source.process is None and not (tmp_path / "energy.json").exists()
    with pytest.raises(EnergyError, match="manafa_not_started"):
        source.joules({"measured"}, "c", tmp_path, "d", tmp_path, None, "o")


def test_the_session_keeps_manafa_noise_out_of_its_answers(tmp_path, monkeypatch):
    run_window(manafa(monkeypatch), tmp_path)
    assert "noise on stdout from manafa" in (tmp_path / "manafa" / "manafa.log").read_text()
