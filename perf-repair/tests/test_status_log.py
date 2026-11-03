"""log/status.py: the status view, a line per outcome keyed by its code word; one fake guide run end to end."""
import logging

import pytest
from test_guide import F, _from_root
from test_guide_targets import FAKE_ROOT, base  # noqa: F401  the guide over fake apps
from test_stages import run  # noqa: F401  the recorded run, grouped

from perfrepair import failure
from perfrepair import run_dir as rd
from perfrepair.app.facts.path_id import path_id
from perfrepair.dto.site import NOT_ON_DEVICE_STEP
from perfrepair.files import read_json
from perfrepair.run_dir import AppPaths
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
    assert [line for line in lines if line] == [
        "run r1 2026-11-03T00:00:00.000Z: guide --device",
        "no_options app a at dossier: none of 2 scopes has an option",
        "reused app b",
        "missing_device_stage guide grouping: 2 of 2 items have no decision",
        "ran device probe: no manifest.yaml",
        "failed device benchmark: BenchmarkRunError: pipeline exited 1 (device); last error: crashed",
        "missing_file error: x.json",
        f"bug run bug: KeyError: 'k'; traceback in {rd.BUG_LOG}",
        "end r1: exit 1 (1.5s)"]


def test_a_finding_names_its_code_item_app_and_where_to_look():
    e = ev("device", "pipeline", FINDING, item="device", outcome="pipeline_failed", detail="exit 3; error: x",
           ref="log/pipeline/r1.log")
    assert status_line(e) == "pipeline_failed device: exit 3; error: x; see log/pipeline/r1.log"
    e = ev("device", "measures", FINDING, item="energyJ", outcome="perf_mode_unmeasured",
           detail="perf_mode_unmeasured: energyJ is selected but c.yaml does not set it")
    assert status_line(e) == "perf_mode_unmeasured energyJ: energyJ is selected but c.yaml does not set it"


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
    transcript = f"{rd.PIPELINE_LOGS}/{last[0].split()[1]}.log"
    at = (base.run_dir / transcript).read_text().splitlines().index(f"# device app {pb}") + 1
    case = read_json(AppPaths(base.run_dir, pa).scoped_benchmark)["cases"][1]["id"]
    missing = [f"not_on_device {name} app {{}}: 1 sites; {NOT_ON_DEVICE_STEP}" for name in ("Bundled", "KeyStore AndroidKeyStore")]
    assert last[0].startswith("run ") and last[-1].startswith("end ") and ": exit 1 (" in last[-1]
    assert last[1:-1] == [
        "reused device grouping: every item decided, saved files current",
        *(m.format(pa) for m in missing),
        f"short_window {case} app {pa}: energy_invalid: short_window; see {pa}/measured/scoped/energy.json",
        f"ok app {pa}",
        *(m.format(pb) for m in missing),
        f"pipeline_failed device app {pb}: exit 1; error: no_scope_compiled: every scope is not_compilable; "
        f"see {transcript}:{at}",
        f"device_failed app {pb} at device: pipeline exited 1 (device); full log {base.run_dir / transcript}:{at}"
        "; last error: no_scope_compiled: every scope is not_compilable"]
    lines = (base.run_dir / transcript).read_text().splitlines()
    assert lines[at - 1] == f"# device app {pb}" and lines[0] == f"# device app {pa}"


def test_a_first_run_whose_pipeline_fails_still_reports_it_in_the_device_folder(tmp_path, capsys, logger, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(F / "device"))
    monkeypatch.setenv("FAKE_INTERRUPT", "1")
    code, _ = _from_root(tmp_path, capsys)
    device = tmp_path / "results" / "fake-api36-00000000"
    status = (device / rd.STATUS_LOG).read_text().splitlines()
    assert code == 1 and not (device / rd.MANIFEST).exists()
    assert [line.split()[0] for line in status] == ["run", "pipeline_failed", "failed", "prerequisites_failed", "end"]
    transcript = f"{rd.PIPELINE_LOGS}/{status[0].split()[1]}.log"
    assert status[1] == f"pipeline_failed configure: exit 1; error: interrupted; see {transcript}:1"
    assert (device / transcript).is_file()
