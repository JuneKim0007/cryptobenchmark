"""Each static step's start and end events with its counts and file digests, on the guide's two fixture chains."""
import pytest
from test_guide import APP, F, FAKE_ROOT, _from_root, first_option, guide, run_steps
from test_stages import run  # noqa: F401  the recorded run, grouped

from perfrepair import run_dir as rd
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.failure import reported
from perfrepair.files import sha256_file
from perfrepair.log import attach
from perfrepair.log.read import read_events


def _ends(events, stage, step=None):
    return [e for e in events if e.stage == stage and e.event == "end" and step in (None, e.step)]


def test_the_device_stage_says_per_stage_whether_it_ran_and_why_then_reused(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(F / "device"))
    _from_root(tmp_path, capsys)
    device = tmp_path / "results" / "fake-api36-00000000"
    events = read_events(device / rd.EVENTS)
    assert events[0].event == "run_start" and events[-1].event == "run_end" and events[-1].outcome == "exit 1"
    assert [(e.step, e.outcome, e.detail) for e in _ends(events, "device")] == [
        ("benchmark", "ran", "probe reruns"), ("probe", "ran", "no manifest.yaml"),
        ("inbound", "ran", "benchmark reruns"), ("screen", "ran", "probe reruns"), ("grouping", "ran", "")]
    _from_root(tmp_path, capsys)
    again = [e for e in read_events(device / rd.EVENTS) if e.run != events[0].run]
    assert [(e.step, e.outcome) for e in _ends(again, "device")] == [(s, "reused") for s in
                                                                    ("probe", "benchmark", "inbound", "screen", "grouping")]


@pytest.mark.usefixtures("asked_by_model")
def test_inbound_build_screen_assign_report_app_and_dossier_end_with_counts(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(F / "device"))
    _from_root(tmp_path, capsys)
    device = tmp_path / "results" / "fake-api36-00000000"
    events = read_events(device / rd.EVENTS)
    inbound = _ends(events, "inbound")[0]
    assert set(inbound.data["counts"]) == {"rows", "logEntries", "records", "warnings"}
    build = _ends(events, "grouping", "build")[0]
    assert set(build.data["counts"]) == {"items", "verdicts", "codeGrouped", "signatureGrouped"}
    assert build.data["files"] == {f"grouping/{n}": sha256_file(device / "grouping" / n)
                                   for n in ("screen.json", "profiles.json", "items.json")}
    screen = _ends(events, "screening", "screen")[0]
    assert sum(screen.data["counts"].values()) == build.data["counts"]["verdicts"]
    assign = [e for e in events if e.stage == "grouping" and e.step == "assign"]
    assert assign[0].event == "start" and assign[-1].event == "end" and assign[0].kind == "model"
    assert {e.event for e in assign} == {"start", "turn", "decision", "end"} and all(e.tokens is None for e in assign)
    assert _ends(events, "grouping", "report")[0].data["counts"]["groups"] >= 1
    app = [e for e in events if e.stage == "app" and e.event == "end"]
    assert [e.step for e in app] == ["detect", "scope"] and app[0].app == app[1].app
    assert app[0].data["counts"]["sites"] >= 1 and "scopes" in app[1].data["counts"]
    dossier = _ends(events, "repair", "dossier")[0]
    assert dossier.data["counts"]["dossiers"] == 0 and dossier.data["counts"]["noOptions"]
    guide_steps = [(e.step, e.outcome) for e in events if e.stage == "guide" and e.step not in ("target", "summary")]
    assert guide_steps[-1] == ("dossier", "stop") and all(o == "ok" for _, o in guide_steps[:-1])


def test_replace_edit_harness_and_report_end_with_counts(run, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(FAKE_ROOT))
    attach()
    g, _ = guide(run, ScriptedConversations(first_option(run)))
    # as the guide's command runs it: the commands it calls in-process join its run
    assert reported(lambda: (attach(run), run_steps(g, device=True))[1]) == 0
    events = read_events(run / rd.EVENTS)
    replace = [e for e in events if e.stage == "replace" and e.event == "decision"]
    assert replace and all(e.app == g.app_id and e.ref.startswith(f"{g.app_id}/replace/outbox/") for e in replace)
    edit = _ends(events, "repair", "edit")[0].data
    assert edit["counts"]["applied"] >= 1 and edit["files"] == {f"{g.app_id}/edits.json": sha256_file(g.paths.edits)}
    assert _ends(events, "repair", "harness")[0].data["counts"]["scopes"] >= 1
    report = _ends(events, "report", "app")[0]
    assert report.app == g.app_id and report.data["counts"]["measured"] >= 1
    assert APP.is_dir()
