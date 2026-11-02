"""The guide end to end on the fixtures: recorded results, the demo app, scripted model answers, no device."""
import shutil
import sys
from pathlib import Path

import pytest
import yaml
from helpers import LIBRARY
from repair_fixture import digests
from test_stages import run  # noqa: F401  the recorded run, grouped

from perfrepair.__main__ import main as top
from perfrepair.ai.parse.grouping_assign import command as assign_cmd
from perfrepair.ai.parse.grouping_assign.kind import GroupingKind, charter
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.runtime.engine.decide import decide
from perfrepair.ai.suggest.site_replace.command import DRY_RUN
from perfrepair.dto.site import Dossier, required_risks
from perfrepair.files import read_json
from perfrepair.grouping.paths import GroupingPaths
from perfrepair.grouping.report.checks import report
from perfrepair.guide.command import run_steps
from perfrepair.guide.steps import Guide
from perfrepair.result.modes import MODES
from perfrepair.run_dir import AppPaths
from perfrepair.check.run import validate_run
from perfrepair.validation.suggest.site_replace import required_kinds, takes

F = Path(__file__).parent / "fixtures"
APP, RESULTS, FAKE_ROOT = F / "app", F / "results", F / "guide"
SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
FIELD = {"set_provider": "provider", "set_algorithm": "algorithm"}


def first_option(run_dir, app_root=None):
    """A model that replaces each scope with its first option and states exactly the edits and risks the gate wants;
    with app_root, it also shifts the scope's file by a line, so the edit can no longer find the call."""
    def answer(task, *_):
        doc = read_json(AppPaths(run_dir, "demo").dossiers)
        d = next(Dossier.from_json(x) for x in doc["dossiers"] if x["scope"]["id"] == task.item)
        o = d.options[0]
        edits = []
        for kind in required_kinds(o, d.current):
            value = takes(kind, o.item, o.pins)
            e = {"kind": kind, "provider": "", "algorithm": "", "parameters": []}
            if kind == "pin_parameters":
                e["parameters"] = [{"name": k, "value": str(v)} for k, v in value.items()]
            else:
                e[FIELD[kind]] = value
            edits.append(e)
        if app_root is not None:
            path = app_root / d.scope.file
            path.write_text("\n" + path.read_text())
        return {"decision": "replace", "option": o.alias, "edits": edits, "risks": sorted(required_risks(d.scope, o)),
                "reason": "faster"}
    return answer


def guide(run_dir, conversations, app=APP, results=RESULTS, config=None):
    lines = []
    g = Guide(run_dir, app, "demo", results, MODES["latency"], conversations, LIBRARY, config=config, echo=lines.append)
    return g, lines


def statuses(lines):
    return [l.split(":")[0] + ":" + l.split(":")[1] for l in lines if l.startswith("guide ")]


def test_the_dry_guide_chains_every_step_to_a_harness_cryptobenchmark_reads(run):
    before = digests(APP)
    g, lines = guide(run, ScriptedConversations(first_option(run)))
    assert run_steps(g, device=False) == 0
    assert statuses(lines) == ["guide prerequisites: ok", "guide app: ok", "guide dossier: ok", "guide replace: ok",
                               "guide edit: ok", "guide harness: ok"]
    assert digests(APP) == before
    assert all(not problems for problems in validate_run(run).values())
    harness = yaml.safe_load(g.paths.harness.read_text())
    assert harness["scopes"] and all(s["current"] != s["option"] for s in harness["scopes"])
    sys.path.insert(0, str(SCRIPTS))
    import scope_generate, scope_harness
    read = scope_harness.read(g.paths.harness)
    assert {s.id: (s.current, s.option) for s in read.scopes} == {s["id"]: (s["current"], s["option"])
                                                                   for s in harness["scopes"]}
    plan, _ = scope_generate.generate(g.paths.harness, run / "root", run / "scoped", compiler=lambda root: [])
    records = yaml.safe_load(plan.read_text())["scopes"]
    assert {r["id"] for r in records} == {s["id"] for s in harness["scopes"]}
    assert all(r["current"] for r in records)


def test_the_device_guide_measures_through_the_pipeline_and_reports(run, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(FAKE_ROOT))
    g, lines = guide(run, ScriptedConversations(first_option(run)))
    assert run_steps(g, device=True) == 0
    assert statuses(lines)[-2:] == ["guide device: ok", "guide report: ok"]
    doc = read_json(g.paths.report)
    measured = [s for s in doc["scopes"] if s["interop"]["status"] == "passed"]
    assert measured and doc["funnel"]["measured"] == len(measured)
    time = measured[0]["metrics"][0]
    assert (time["metric"], time["before"], time["after"], time["ratio"]) == ("timeNs", 1000, 800, 0.8)
    assert measured[0]["verdict"] == "improves"
    assert all(not problems for problems in validate_run(run).values())


def test_a_failing_device_run_stops_with_its_code(run, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(FAKE_ROOT))
    monkeypatch.setenv("FAKE_EXIT", "3")
    g, lines = guide(run, ScriptedConversations(first_option(run)))
    assert run_steps(g, device=True) == 1
    assert lines[-1].startswith("guide device: stop device_failed: pipeline exited 3")
    assert not g.paths.report.exists()


def test_results_without_a_manifest_stop_first(run, tmp_path):
    g, lines = guide(run, DRY_RUN, results=tmp_path)
    assert run_steps(g, device=False) == 1
    assert lines == [f"guide prerequisites: stop missing_results: {tmp_path / 'manifest.yaml'} absent; "
                     "--results is a cryptobenchmark results directory"]


def test_a_run_without_grouping_says_how_to_make_it(run):
    GroupingPaths(run).groups.unlink()
    g, lines = guide(run, DRY_RUN)
    assert run_steps(g, device=False) == 1
    assert "stop missing_run_stage" in lines[-1] and "grouping assign --run <run>" in lines[-1]


def test_singleton_groups_leave_no_options(tmp_path):
    from perfrepair.data_handler.inbound.__main__ import main as inbound
    from perfrepair.grouping.build.stage import build_stage
    assert inbound(["--manifest", str(RESULTS / "manifest.yaml"), "-o", str(tmp_path)]) == 0
    build_stage(RESULTS / "manifest.yaml", tmp_path)
    paths = GroupingPaths(tmp_path)
    decide(GroupingKind(paths), charter(LIBRARY), assign_cmd.DRY_RUN, paths.root, echo=lambda _: None)
    report(paths)
    g, lines = guide(tmp_path, DRY_RUN)
    assert run_steps(g, device=False) == 1
    assert lines[-1].startswith("guide dossier: stop no_options: none of 11 scopes has an option")


def test_a_model_that_keeps_everything_stops_before_the_edit(run):
    g, lines = guide(run, DRY_RUN)
    assert run_steps(g, device=False) == 1
    assert lines[-1].startswith("guide replace: stop no_replacement")
    assert not g.paths.edits.exists()


def test_edits_that_cannot_find_their_call_stop_with_the_reasons(run, tmp_path):
    app = tmp_path / "app"
    shutil.copytree(APP, app)
    g, lines = guide(run, ScriptedConversations(first_option(run, app)), app=app)
    assert run_steps(g, device=False) == 1
    assert lines[-1].startswith("guide edit: stop no_edit_applied") and "(function_span)" in lines[-1]


def test_the_top_level_command_names_its_commands(capsys):
    assert top([]) == 2
    assert "python3 -m perfrepair {guide}" in capsys.readouterr().err


def test_a_bad_app_name_is_a_coded_stop(run):
    lines = []
    g = Guide(run, APP, "../x", RESULTS, MODES["latency"], DRY_RUN, LIBRARY, echo=lines.append)
    assert run_steps(g, device=False) == 1
    assert lines[-1].startswith("guide prerequisites: stop prerequisites_failed: app name '../x'")


@pytest.fixture(autouse=True)
def _scripts_off_path():
    yield
    if str(SCRIPTS) in sys.path:
        sys.path.remove(str(SCRIPTS))

