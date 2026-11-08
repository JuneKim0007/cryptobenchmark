"""The guide end to end on the fixtures: recorded results, the demo app, scripted model answers, no device."""
import json
import shutil
import sys
from dataclasses import replace as with_field
from pathlib import Path

import pytest
import yaml
from helpers import captured_events, first_candidate, guide_ends, with_results, LIBRARY
from repair_fixture import digests
from test_stages import run  # noqa: F401  the recorded run, grouped

from perfrepair import run_dir as rd
from perfrepair.__main__ import main as top
from perfrepair.ai.parse.grouping_assign import command as assign_cmd
from perfrepair.ai.parse.grouping_assign.kind import GroupingKind, charter
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.runtime.engine.decide import decide
from perfrepair.ai.select.command import dry_run
from perfrepair.ai.runtime.engine.outbox import active_outbox
from perfrepair.files import read_json, write_json
from perfrepair.run_dir import GroupingPaths
from perfrepair.grouping.report.checks import report
from perfrepair.guide.run import run_app, run_sequence
from perfrepair.guide.device_steps import DEVICE_LEVEL
from perfrepair.guide.state import Guide
from helpers import LATENCY
from perfrepair.run_dir import AppPaths
from perfrepair.check.run import validate_run
from perfrepair.validation.dossiers.parse import parse_dossiers
from perfrepair.screen.catalog import screening_catalog
from perfrepair.app.facts.path_id import path_id

F = Path(__file__).parent / "fixtures"
APP, RESULTS, FAKE_ROOT = F / "app", F / "results" / "test-api36-00000000", F / "guide"
SCRIPTS = Path(__file__).resolve().parents[3] / "apps/benchmark-runner"


ENDS = []


def run_steps(g, device):
    """The device-level steps, then the one app g names; ENDS holds the guide steps they ended."""
    with captured_events() as events:
        code = 1 if run_sequence(g, DEVICE_LEVEL) or run_app(g, device) else 0
    ENDS[:] = guide_ends(events)
    return code


def stopped():
    """The step the last run stopped at, with its code."""
    return [(step, code) for step, outcome, code in ENDS if outcome == "stop"][-1]


def first_option(run_dir, app_root=None):
    """A model that takes each item's first candidate; with app_root, it also shifts a unit's file by a line, so the edit
    can no longer find the call."""
    def answer(task, *_):
        doc = read_json(AppPaths(run_dir, path_id(app_root or APP)).dossiers)
        unit = next((u for u in parse_dossiers(doc, doc["app"])[0] if u.key == task.item), None)
        if app_root is not None and unit is not None:
            path = app_root / unit.dossiers[0].scope.file
            path.write_text("\n" + path.read_text())
        return first_candidate(task)
    return answer



def guide(run_dir, conversations, app=APP, config=None):
    return Guide(run_dir, app, LATENCY, conversations, LIBRARY, config=config, echo=lambda _: None)


def test_the_dry_guide_chains_every_step_to_a_harness_cryptobenchmark_reads(run):
    before = digests(APP)
    g = guide(run, ScriptedConversations(first_option(run)))
    assert run_steps(g, device=False) == 0
    assert {(step, outcome) for step, outcome, _ in ENDS} == {(s, "ok") for s in (
        "prerequisites", "targets", "grouping", "interop", "app", "dossier", "upgrade", "replace", "edit", "harness")}
    assert digests(APP) == before
    assert all(not problems for problems in validate_run(run, screening_catalog(None)).values())
    harness = yaml.safe_load(g.paths.harness.read_text())
    assert harness["scopes"] and all(s["current"] != s["option"] for s in harness["scopes"])
    sys.path.insert(0, str(SCRIPTS))
    from scope import generate as scope_generate
    from scope import harness as scope_harness
    read = scope_harness.read(g.paths.harness)
    assert {s.id: (s.current, s.option) for s in read.scopes} == {s["id"]: (s["current"], s["option"])
                                                                   for s in harness["scopes"]}
    plan, _ = scope_generate.generate(g.paths.harness, run / "root", run / "scoped", compiler=lambda root: [])
    records = yaml.safe_load(plan.read_text())["scopes"]
    assert {r["id"] for r in records} == {s["id"] for s in harness["scopes"]}
    assert all(r["current"] for r in records)
    assert all(r["inputs"] == {"inputSize": 1024, "keySize": 128, "from": "run"} for r in records)
    by_function = {}
    for r in records:
        by_function.setdefault(r["function"], []).append((r["status"], r.get("reason")))
    # the other seal's option is slower on every metric: rejected no_gain, so it is not asked
    assert by_function == {"seal": [("compiled", None)]}


def test_the_device_guide_checks_through_the_pipeline_and_reports(run, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(FAKE_ROOT))
    g = guide(run, ScriptedConversations(first_option(run)))
    assert run_steps(g, device=True) == 0
    assert {("device", "ok", None), ("report", "ok", None)} <= set(ENDS)
    doc = read_json(g.paths.report)
    passed = [s for s in doc["scopes"] if s["interop"]["status"] == "passed"]
    assert passed and doc["funnel"]["interopPassed"] == len(passed)
    assert passed[0]["inputs"] == {"inputSize": 1024, "keySize": 128, "from": "run"}
    assert "- inputs: input 1024 B, key 128 bits, from run" in g.paths.report_md.read_text()
    assert all(not problems for problems in validate_run(run, screening_catalog(None)).values())


def _damage_yaml(path, field="schemaVersion"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({field: 0}))


def _damage_manifest(path):
    path.write_text(yaml.safe_dump({**yaml.safe_load(path.read_text()), "files": {"ghost": "no-such-file"}}))


def _damage_json(path):
    write_json(path, {**read_json(path), "app": "another"})


def _damage_decision(path):
    doc = read_json(path)
    doc["replacements"][0]["decision"] = "swap"
    write_json(path, doc)


@pytest.mark.parametrize("artifact, damage, problem", [
    (lambda g: rd.MANIFEST, _damage_manifest, "does not exist"),
    (lambda g: rd.PRIMITIVES_MISSING, _damage_yaml, "schemaVersion"),
    (lambda g: rd.BENCHMARK_COVERAGE, _damage_yaml, "schemaVersion"),
    (lambda g: f"{g.app_id}/{rd.REPLACEMENTS}", _damage_decision, "is not one of"),
    (lambda g: f"{g.app_id}/{rd.EDITS}", _damage_json, "another"),
    (lambda g: f"{g.app_id}/{rd.HARNESS}", _damage_yaml, "schema"),
], ids=["manifest", "primitives_missing", "benchmark_coverage", "replacements", "edits", "harness"])
def test_the_replay_checks_each_artifact_it_used_to_skip_and_finds_it_damaged(run, artifact, damage, problem):
    g = guide(run, ScriptedConversations(first_option(run)))
    assert run_steps(g, device=False) == 0
    name = artifact(g)
    assert validate_run(run, screening_catalog(None)).get(name, []) == []
    damage(run / name)
    assert any(problem in p for p in validate_run(run, screening_catalog(None))[name])


def test_a_malformed_repair_file_is_its_problem_in_the_replay(run):
    g = guide(run, ScriptedConversations(first_option(run)))
    assert run_steps(g, device=False) == 0
    (g.paths.replacements).write_text("[1]")
    assert "does not parse" in validate_run(run, screening_catalog(None))[f"{g.app_id}/{rd.REPLACEMENTS}"][0]


def test_a_failing_device_run_stops_with_its_code(run, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(FAKE_ROOT))
    monkeypatch.setenv("FAKE_EXIT", "3")
    g = guide(run, ScriptedConversations(first_option(run)))
    assert run_steps(g, device=True) == 1
    assert stopped() == ("device", "pipeline_failed")
    assert not g.paths.report.exists()


def test_a_run_without_grouping_says_how_to_make_it(run):
    shutil.rmtree(GroupingPaths(run).root)
    g = guide(run, dry_run())
    assert run_steps(g, device=False) == 1
    assert stopped() == ("grouping", "missing_device_stage")


@pytest.mark.usefixtures("asked_by_model")
def test_a_named_folder_with_items_undecided_asks_them(run):
    shutil.rmtree(GroupingPaths(run).root / "outbox")
    g = guide(run, dry_run())
    g = with_field(g, grouping_args=("--agent", "dry-run"))
    run_steps(g, device=False)
    assert ("grouping", "ok", None) in ENDS and active_outbox(GroupingPaths(run).root).records()


def test_a_named_folder_whose_groups_json_went_missing_is_rebuilt_with_no_call(run):
    GroupingPaths(run).groups.unlink()
    g = guide(run, ScriptedConversations(first_option(run)))
    assert run_steps(g, device=False) == 0
    assert GroupingPaths(run).groups.is_file()


@pytest.mark.usefixtures("asked_by_model")
def test_singleton_groups_leave_no_options(tmp_path):
    from perfrepair.data_handler.inbound.__main__ import main as inbound
    from perfrepair.grouping.build.stage import build_stage
    assert inbound(["--device-results", str(with_results(tmp_path))]) == 0
    build_stage(RESULTS / "manifest.yaml", tmp_path, screening_catalog(None))
    paths = GroupingPaths(tmp_path)
    decide(GroupingKind(paths), charter(LIBRARY), assign_cmd.dry_run(), paths.root, echo=lambda _: None)
    report(paths)
    g = guide(tmp_path, dry_run())
    assert run_steps(g, device=False) == 1
    assert stopped() == ("dossier", "no_options")


def test_a_model_that_keeps_everything_stops_before_the_edit(run):
    g = guide(run, dry_run())
    assert run_steps(g, device=False) == 1
    assert stopped() == ("replace", "no_replacement")
    assert not g.paths.edits.exists()


def test_edits_that_cannot_find_their_call_stop_with_the_reasons(run, tmp_path):
    app = tmp_path / "app"
    shutil.copytree(APP, app)
    g = guide(run, ScriptedConversations(first_option(run, app)), app=app)
    assert run_steps(g, device=False) == 1
    assert stopped() == ("edit", "no_edit_applied")


def test_a_missing_screening_catalog_stops_the_guide_before_any_step(run, tmp_path):
    from perfrepair.config.load import load
    settings = tmp_path / "perfrepair.yaml"
    settings.write_text(f"device:\n  screening:\n    catalog: {tmp_path / 'absent.yaml'}\n")
    g = guide(run, dry_run())
    g.settings = load(settings, {}, {})
    assert run_steps(g, device=False) == 1
    assert ENDS == [("prerequisites", "stop", "prerequisites_failed")]


def test_a_folder_of_several_project_roots_is_a_coded_stop(run, tmp_path):
    for name in ("a", "b"):
        shutil.copytree(APP, tmp_path / "mono" / name)
    g = guide(run, dry_run(), app=tmp_path / "mono")
    assert run_steps(g, device=False) == 1
    assert stopped() == ("app", "several_project_roots")


def _from_root(tmp_path, capsys):
    settings = tmp_path / "perfrepair.yaml"
    if not settings.exists():
        settings.write_text("{}\n")
        (tmp_path / "global.yaml").write_text("schemaVersion: 1\nproviders: {bundled: []}\n")
    code = top(["guide", "--app", str(APP), "--agent", "dry-run", "--perf-mode", "latency,throughput", "--perfrepair-config", str(settings),
                "--config", str(tmp_path / "global.yaml"), "--results-root", str(tmp_path / "results")])
    events = [json.loads(e) for e in (tmp_path / "results" / "fake-api36-00000000" / rd.EVENTS).read_text().splitlines()]
    last = [e for e in events if e["run"] == events[-1]["run"]]
    return code, {(e["stage"], e["step"], e["outcome"], e["data"].get("code")) for e in last if e["event"] in ("end", "finding")}


@pytest.mark.usefixtures("asked_by_model")
def test_without_a_named_device_the_guide_makes_the_device_stage_then_reuses_it(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(F / "device"))
    code, first = _from_root(tmp_path, capsys)
    # stops.bundled_missing warn: the demo app ships a provider the fake device lacks, and the run goes on
    assert code == 1 and ("device", "bundled", "warn", "bundled_missing") in first
    assert {("device", "probe", "ran", None), ("device", "grouping", "ran", None)} <= first
    stops = {e for e in first if e[2] == "stop"}
    assert stops == {("guide", "dossier", "stop", "no_options"), ("guide", "target", "stop", "no_options")}
    device = tmp_path / "results" / "fake-api36-00000000"
    decided = sorted((device / "grouping" / "outbox").rglob("*.json"))
    assert decided
    code, again = _from_root(tmp_path, capsys)
    assert code == 1 and {("device", s, "reused", None) for s in ("probe", "benchmark", "inbound", "screen", "grouping")} <= again
    assert {e for e in again if e[2] == "stop"} == stops
    # device.filterByApps: a probe, then the benchmark of the used set
    assert len((tmp_path / "results" / "runs.log").read_text().splitlines()) == 2
    assert sorted((device / "grouping" / "outbox").rglob("*.json")) == decided


@pytest.fixture(autouse=True)
def _scripts_off_path():
    yield
    if str(SCRIPTS) in sys.path:
        sys.path.remove(str(SCRIPTS))


def test_a_blocking_invariant_stops_before_the_replace_call(request, monkeypatch):
    from perfrepair.guide import app_steps
    from perfrepair.validation.finding import ADVISORY, BLOCKING, Violation
    found = [Violation("key_contract_agrees", BLOCKING, "group g1", ("group g1",), "split it"),
             Violation("interop_not_run", ADVISORY, "group g2", ("group g2",), "run it")]
    monkeypatch.setattr(app_steps, "app_gate", lambda device, app, root: found)
    g = guide(request.getfixturevalue("run"), dry_run())
    assert run_steps(g, device=False) == 1
    assert stopped() == ("replace", "invariant_failed")
    assert not g.paths.replace.exists()


@pytest.mark.parametrize("chosen", [None, "stop"])
def test_an_undecided_invariant_warns_by_default_and_stops_when_set(run, tmp_path, monkeypatch, chosen):
    from perfrepair.guide import app_steps
    from perfrepair.validation.finding import UNDECIDED, Violation
    roots = []
    found = [Violation("site_line_holds_call", UNDECIDED, "scope s1", ("A.java:3", "no source"), "check it by hand")]
    monkeypatch.setattr(app_steps, "app_gate", lambda device, app, root: roots.append(root) or found)
    if chosen:
        (tmp_path / "perfrepair.yaml").write_text(f"stops: {{invariant_undecided: {chosen}}}\n")
        monkeypatch.setenv("PERFREPAIR_CONFIG", str(tmp_path / "perfrepair.yaml"))
    g = guide(run, ScriptedConversations(first_option(run)))
    with captured_events() as events:
        assert run_steps(g, device=False) == (1 if chosen else 0)
    [event] = [e for e in events if e.event == "finding" and e.data.get("code") == "invariant_undecided"]
    assert event.outcome == (chosen or "warn") and "site_line_holds_call scope s1" in event.detail
    assert roots == [APP] and g.paths.replace.exists() is not bool(chosen)
