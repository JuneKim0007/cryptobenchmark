"""log/status.py: the status view, a line per outcome keyed by its code word; one fake guide run end to end."""
import logging

import pytest
from test_guide import F, _from_root
from test_guide_targets import FAKE_ROOT, base  # noqa: F401  the guide over fake apps
from test_stages import run  # noqa: F401  the recorded run, grouped

from perfrepair import failure
from perfrepair import run_dir as rd
from perfrepair.app.facts.path_id import path_id
from perfrepair.dto.event import BUG, END, ERROR, FINDING, RUN_END, RUN_START, Event
from perfrepair.log import attach
from perfrepair.log.attach import SINK
from perfrepair.log.read import read_events
from perfrepair.log.status import code_of, status_line
from perfrepair.log.views import render


def ev(stage, step, event, **kw):
    return Event("2026-11-03T00:00:00.000Z", "r1", stage, step, event, **kw)


@pytest.mark.parametrize("text,code", [
    ("no_options: none of 3 scopes", "no_options"), ("missing_device_stage at grouping", "missing_device_stage"),
    ("bug: x", "bug"), ("pipeline exited 1 (device)", "fallback"), ("none of 46 scopes", "fallback"), ("", "fallback")])
def test_a_code_is_an_underscored_word_or_a_word_before_a_colon(text, code):
    assert code_of(text, "fallback") == code


def test_each_line_kind_starts_with_its_code_word():
    lines = [status_line(e) for e in (
        ev("run", "guide", RUN_START, detail="guide --device"),
        ev("guide", "target", END, app="a", outcome="stop", detail="no_options at dossier: none of 2 scopes has an option",
           data={"code": "no_options", "step": "dossier"}),
        ev("guide", "target", END, app="b", outcome="reused"),
        ev("guide", "grouping", END, outcome="stop", detail="missing_device_stage: 2 of 2 items have no decision"),
        ev("guide", "dossier", END, app="a", outcome="stop", detail="no_options: per app, the target line says it"),
        ev("device", "probe", END, outcome="ran", detail="no manifest.yaml"),
        ev("device", "benchmark", END, outcome="failed", detail="BenchmarkRunError: pipeline exited 1 (device); last lines:\n"
                                                                "warning: w\nerror: crashed\nmore"),
        ev("device", "selection", END, outcome="ok"),
        ev("run", "error", ERROR, outcome="error", detail="missing_file: x.json"),
        ev("run", "bug", BUG, outcome="bug", detail="KeyError: 'k'"),
        ev("run", "guide", RUN_END, outcome="exit 1", durationMs=1500))]
    assert [line.split()[0] for line in lines if line] == [
        "run", "no_options", "reused", "missing_device_stage", "ran", "failed", "missing_file", "bug", "end"]


def test_an_end_whose_halt_terminate_reported_has_no_line_of_its_own():
    reported = {"code": "pipeline_failed", "reported": True}
    assert [status_line(e) for e in (
        ev("device", "probe", END, outcome="failed", detail="Halt: pipeline_failed: x", data=reported),
        ev("guide", "prerequisites", END, outcome="stop", detail="pipeline_failed: x", data=reported),
        ev("guide", "target", END, app="a", outcome="stop", detail="pipeline_failed: x", data=reported))] == [None] * 3


def test_a_finding_names_its_code_item_app_and_where_to_look():
    e = ev("device", "pipeline", FINDING, item="device", outcome="pipeline_failed", detail="exit 3; error: x",
           ref="log/pipeline/r1.log")
    assert status_line(e).startswith("pipeline_failed device") and "log/pipeline/r1.log" in status_line(e)
    e = ev("device", "measures", FINDING, item="energyJ", outcome="perf_mode_unmeasured",
           detail="perf_mode_unmeasured: energyJ is selected but c.yaml does not set it")
    assert status_line(e).startswith("perf_mode_unmeasured energyJ")


@pytest.fixture
def logger():
    root = logging.getLogger("perfrepair")
    before, level = list(root.handlers), root.level
    root.handlers[:] = []
    yield
    SINK.close()
    root.handlers[:], root.level = before, level


def test_a_guide_run_renders_exactly_its_outcomes(base, logger, monkeypatch):  # noqa: F811
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(FAKE_ROOT))
    a, b = base.app("a"), base.app("b")
    monkeypatch.setenv("FAKE_ENERGY_INVALID", "1")
    monkeypatch.setenv("FAKE_FAIL_APP", path_id(b))
    attach()
    assert failure.reported(lambda: (attach(base.run_dir), base.go([a, b], device=True)[0])[1]) == 1
    status = (base.run_dir / rd.STATUS_LOG).read_text().splitlines()
    assert status == render(read_events(base.run_dir / rd.EVENTS))[rd.STATUS_LOG]
    last = status[max(n for n, line in enumerate(status) if line.startswith("run ")):]
    pa, pb = path_id(a), path_id(b)
    assert ": exit 1 (" in last[-1]
    words = {line.split()[0] for line in last}
    assert {"interop_unverified", "not_on_device", "energy_invalid", "ok", "pipeline_failed"} <= words
    failed = next(line for line in last if line.startswith("pipeline_failed "))
    assert f"app {pb}" in failed and f"ok app {pa}" in last
    # the failure line points at the transcript line where its device run starts
    transcript, at = failed.split("see ")[1].split(";")[0].rsplit(":", 1)
    assert (base.run_dir / transcript).read_text().splitlines()[int(at) - 1] == f"# device app {pb}"


def test_a_first_run_whose_pipeline_fails_still_reports_it_in_the_device_folder(tmp_path, capsys, logger, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(F / "device"))
    monkeypatch.setenv("FAKE_INTERRUPT", "1")
    code, _ = _from_root(tmp_path, capsys)
    device = tmp_path / "results" / "fake-api36-00000000"
    status = (device / rd.STATUS_LOG).read_text().splitlines()
    assert code == 1 and not (device / rd.MANIFEST).exists()
    # one line for the failure: no `failed device probe`, no `prerequisites_failed` after it
    assert [line.split()[0] for line in status] == ["run", "pipeline_failed", "end"]
    assert (device / f"{rd.PIPELINE_LOGS}/{status[0].split()[1]}.log").is_file()
