"""The guide end to end on the fixtures: recorded results, the demo app, scripted model answers, no device."""
import json
import shutil
import sys
from dataclasses import replace as with_field
from pathlib import Path

import pytest
import yaml
from helpers import with_results, LIBRARY
from repair_fixture import digests
from test_stages import run  # noqa: F401  the recorded run, grouped

from perfrepair.__main__ import main as top
from perfrepair.ai.parse.grouping_assign import command as assign_cmd
from perfrepair.ai.parse.grouping_assign.kind import GroupingKind, charter
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.runtime.engine.decide import decide
from perfrepair.ai.suggest.site_replace.command import DRY_RUN
from perfrepair.dto.dossier import Dossier
from perfrepair.dto.replacement import required_risks
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
from perfrepair.validation.suggest.site_replace import check_reply
from perfrepair.validation.suggest.site_edits import required_kinds, takes
from perfrepair.screen.catalog import screening_catalog
from perfrepair.app.facts.path_id import path_id

F = Path(__file__).parent / "fixtures"
APP, RESULTS, FAKE_ROOT = F / "app", F / "results" / "test-api36-00000000", F / "guide"
SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
FIELD = {"set_provider": "provider", "set_algorithm": "algorithm"}


def run_steps(g, device):
    """The device-level steps, then the one app g names."""
    return 1 if run_sequence(g, DEVICE_LEVEL) or run_app(g, device) else 0


def first_option(run_dir, app_root=None):
    """A model that replaces each scope with its first option and states exactly the edits and risks the gate wants;
    with app_root, it also shifts the scope's file by a line, so the edit can no longer find the call."""
    def answer(task, *_):
        doc = read_json(AppPaths(run_dir, path_id(app_root or APP)).dossiers)
        reply, d = replacing(doc, task)
        if app_root is not None:
            path = app_root / d.scope.file
            path.write_text("\n" + path.read_text())
        return reply
    return answer


def replacing(doc, task):
    """The answer that gives each member with options its first option and the risks the gate wants, and its first dossier."""
    unit = next(u for u in parse_dossiers(doc, doc["app"])[0] if u.key == task.item)
    members = [_first_option(a, d) for a, d in unit.aliased().items()]
    reply = {"decision": "replace", "members": members, "reason": "faster"}
    wants = {p.split(":")[0] for p in check_reply(json.dumps(reply), unit)[1] if "must include unverified_interop" in p}
    for m in members:
        m["risks"] += ["unverified_interop"] if m["member"] in wants else []
    return reply, unit.dossiers[0]


def _first_option(alias, d):
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
    return {"member": alias, "option": o.alias, "edits": edits, "risks": sorted(required_risks(d.scope, o))}


def guide(run_dir, conversations, app=APP, config=None):
    lines = []
    g = Guide(run_dir, app, LATENCY, conversations, LIBRARY, config=config, echo=lines.append)
    return g, lines


def statuses(lines):
    return [l.split(":")[0] + ":" + l.split(":")[1] for l in lines if l.startswith("guide ")]


def test_the_dry_guide_chains_every_step_to_a_harness_cryptobenchmark_reads(run):
    before = digests(APP)
    g, lines = guide(run, ScriptedConversations(first_option(run)))
    assert run_steps(g, device=False) == 0
    assert statuses(lines) == ["guide prerequisites: ok", "guide targets: ok", "guide grouping: ok", "guide app: ok", "guide dossier: ok",
                               "guide replace: ok", "guide edit: ok", "guide harness: ok"]
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
    assert measured[0]["inputs"] == {"inputSize": 1024, "keySize": 128, "from": "run"}
    assert "- inputs: input 1024 B, key 128 bits, from run" in g.paths.report_md.read_text()
    assert all(not problems for problems in validate_run(run, screening_catalog(None)).values())


def test_a_failing_device_run_stops_with_its_code(run, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(FAKE_ROOT))
    monkeypatch.setenv("FAKE_EXIT", "3")
    g, lines = guide(run, ScriptedConversations(first_option(run)))
    assert run_steps(g, device=True) == 1
    assert lines[-1].startswith("guide device: stop pipeline_failed: pipeline exited 3")
    assert not g.paths.report.exists()


def test_results_without_a_manifest_stop_first(tmp_path):
    g, lines = guide(tmp_path, DRY_RUN)
    assert run_steps(g, device=False) == 1
    assert lines == [f"guide prerequisites: stop missing_results: {tmp_path / 'manifest.yaml'} absent; "
                     "--device-results is a folder cryptobenchmark wrote"]


def test_a_run_without_grouping_says_how_to_make_it(run):
    shutil.rmtree(GroupingPaths(run).root)
    g, lines = guide(run, DRY_RUN)
    assert run_steps(g, device=False) == 1
    assert "stop missing_device_stage" in lines[-1] and "grouping assign --device-results <device>" in lines[-1]


@pytest.mark.usefixtures("asked_by_model")
def test_a_named_folder_with_items_undecided_asks_them(run):
    shutil.rmtree(GroupingPaths(run).root / "outbox")
    g, lines = guide(run, DRY_RUN)
    g = with_field(g, grouping_args=("--agent", "dry-run"))
    run_steps(g, device=False)
    assert any(line.startswith("guide grouping: ok: ran: ") and "items asked" in line for line in lines)


def test_a_named_folder_whose_groups_json_went_missing_is_rebuilt_with_no_call(run):
    GroupingPaths(run).groups.unlink()
    g, lines = guide(run, ScriptedConversations(first_option(run)))
    assert run_steps(g, device=False) == 0
    assert any("guide grouping: ok: rebuilt from the kept decisions" in l for l in lines)
    assert GroupingPaths(run).groups.is_file()


@pytest.mark.usefixtures("asked_by_model")
def test_singleton_groups_leave_no_options(tmp_path):
    from perfrepair.data_handler.inbound.__main__ import main as inbound
    from perfrepair.grouping.build.stage import build_stage
    assert inbound(["--device-results", str(with_results(tmp_path))]) == 0
    build_stage(RESULTS / "manifest.yaml", tmp_path, screening_catalog(None))
    paths = GroupingPaths(tmp_path)
    decide(GroupingKind(paths), charter(LIBRARY), assign_cmd.DRY_RUN, paths.root, echo=lambda _: None)
    report(paths)
    g, lines = guide(tmp_path, DRY_RUN)
    assert run_steps(g, device=False) == 1
    assert lines[-1].startswith("guide dossier: stop no_options: none of 12 scopes has an option")
    assert lines[-1].endswith("; not_on_device: add it to providers.bundled in global.yaml and rerun the device stage")


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


def test_a_missing_screening_catalog_stops_the_guide_before_any_step(run, tmp_path):
    from perfrepair.config.load import load
    settings = tmp_path / "perfrepair.yaml"
    settings.write_text(f"device:\n  screening:\n    catalog: {tmp_path / 'absent.yaml'}\n")
    g, lines = guide(run, DRY_RUN)
    g.settings = load(settings, {}, {})
    assert run_steps(g, device=False) == 1
    assert len(lines) == 1 and lines[0].startswith("guide prerequisites: stop") and "missing_file" in lines[0]


def test_a_folder_of_several_project_roots_is_a_coded_stop(run, tmp_path):
    for name in ("a", "b"):
        shutil.copytree(APP, tmp_path / "mono" / name)
    g, lines = guide(run, DRY_RUN, app=tmp_path / "mono")
    assert run_steps(g, device=False) == 1
    assert lines[-1].startswith("guide app: stop several_project_roots: ")


def _from_root(tmp_path, capsys):
    settings = tmp_path / "perfrepair.yaml"
    if not settings.exists():
        settings.write_text("{}\n")
        (tmp_path / "global.yaml").write_text("schemaVersion: 1\nproviders: {bundled: []}\n")
    code = top(["guide", "--app", str(APP), "--agent", "dry-run", "--perf-mode", "latency,throughput", "--perfrepair-config", str(settings),
                "--config", str(tmp_path / "global.yaml"), "--results-root", str(tmp_path / "results")])
    return code, [l for l in capsys.readouterr().out.splitlines() if l.startswith(("device ", "guide "))]


@pytest.mark.usefixtures("asked_by_model")
def test_without_a_named_device_the_guide_makes_the_device_stage_then_reuses_it(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(F / "device"))
    code, first = _from_root(tmp_path, capsys)
    # device.bundled.onMissing warn: the demo app ships a provider the fake device lacks, and the run goes on
    assert code == 1 and first[0].startswith("device bundled_missing: warn: BC (org.bouncycastle:bcprov-jdk18on:1.78; ")
    assert first[1] == "device probe: ran: no manifest.yaml"
    assert any(l.startswith("guide grouping: ok: ran: ") and "items asked" in l for l in first)
    stops = [l for l in first if " stop " in l]
    assert len(stops) == 1 and stops[0].startswith("guide dossier: stop no_options: ")
    device = tmp_path / "results" / "fake-api36-00000000"
    decided = sorted((device / "grouping" / "outbox").rglob("*.json"))
    assert decided
    code, again = _from_root(tmp_path, capsys)
    assert code == 1 and again[1:5] == [f"device {s}: reused" for s in ("probe", "benchmark", "inbound", "screen")]
    assert "guide grouping: ok: reused" in again and [l for l in again if " stop " in l] == stops
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
    monkeypatch.setattr(app_steps, "app_gate", lambda device, app: found)
    g, lines = guide(request.getfixturevalue("run"), DRY_RUN)
    assert run_steps(g, device=False) == 1
    assert lines[-1].startswith("guide replace: stop invariant_failed: 1 blocking: blocking key_contract_agrees group g1")
    assert not g.paths.replace.exists()


def test_a_decision_on_an_earlier_dossier_stops_the_guide_until_refresh(run):
    g, lines = guide(run, ScriptedConversations(first_option(run)))
    assert run_steps(g, device=False) == 0
    outbox = active_outbox(g.paths.replace)
    first = outbox.path(1)
    write_json(first, {**read_json(first), "evidence": "0" * 64})
    lines.clear()
    assert run_steps(g, device=False) == 1
    assert lines[-1].startswith("guide replace: stop dossier_changed") and "(guide --refresh)" in lines[-1]
    lines.clear()
    assert run_steps(with_field(g, refresh=True), device=False) == 0
    assert "guide replace: ok" in statuses(lines)
