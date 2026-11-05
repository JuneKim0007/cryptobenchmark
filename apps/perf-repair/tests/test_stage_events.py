"""The device stage's end events say per stage whether it ran, then that it reused."""
from test_guide import F, _from_root
from test_stages import run  # noqa: F401  the recorded run, grouped

from perfrepair import run_dir as rd
from perfrepair.log.read import read_events


def _ends(events, stage, step=None):
    return [e for e in events if e.stage == stage and e.event == "end" and step in (None, e.step)]


def test_the_device_stage_says_per_stage_whether_it_ran_and_why_then_reused(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(F / "device"))
    _from_root(tmp_path, capsys)
    device = tmp_path / "results" / "fake-api36-00000000"
    events = read_events(device / rd.EVENTS)
    assert events[0].event == "run_start" and events[-1].event == "run_end" and events[-1].outcome == "exit 1"
    ran = {e.step: e.outcome for e in _ends(events, "device")}
    assert {ran[s] for s in ("probe", "benchmark", "inbound", "screen", "primitives", "grouping")} == {"ran"}
    assert [e.outcome for e in events if e.event == "finding" and e.data.get("code") == "bundled_missing"] == ["warn"]
    _from_root(tmp_path, capsys)
    again = [e for e in read_events(device / rd.EVENTS) if e.run != events[0].run]
    reused = {e.step: e.outcome for e in _ends(again, "device")}
    assert {reused[s] for s in ("probe", "benchmark", "inbound", "screen", "primitives", "grouping")} == {"reused"}
