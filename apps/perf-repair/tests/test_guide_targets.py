"""The guide over apps.targets: the device stage once, each app isolated, a line per app, reuse by inputs; scripted model, no device."""
import json
import shutil
from pathlib import Path

import pytest
import yaml
from helpers import first_candidate, model_calls, LIBRARY, captured_events, guide_ends
from test_guide import APP, F, FAKE_ROOT
from test_stages import run  # noqa: F401  the recorded run, grouped

from cryptobench.paths import AppTree
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.runtime.gateway.claude_cli import ClaudeCliError
from perfrepair.ai.select.command import dry_run
from perfrepair.app.facts.path_id import path_id
from perfrepair.app.facts.target_set import resolve_targets
from perfrepair.data_handler.outbound.benchmark_runner import BenchmarkRunError
from perfrepair.files import read_json
from perfrepair.guide import app_steps as guide_steps, finished
from perfrepair.dto.perf_mode import PerfMode
from perfrepair.guide.command import main as guide_main
from perfrepair.guide.device_steps import _measured as measured_by_targets
from perfrepair.inputs.check import target_path, target_perf
from perfrepair.result.modes import mode_of
from perfrepair.guide.state import Guide
from perfrepair.guide.targets import run_targets
from helpers import LATENCY


class Base:
    def __init__(self, run_dir, tmp_path):
        self.run_dir, self.tmp = run_dir, tmp_path
        self.answer = ScriptedConversations(self._first_option)

    def _first_option(self, task, *_):
        return first_candidate(task)

    def app(self, name):
        path = self.tmp / "apps" / name
        if not path.exists():
            shutil.copytree(APP, path)
        return path.resolve()

    def go(self, roots, device=False, reuse=True, conversations=None, app_modes=None):
        """The exit and the run's events."""
        base = Guide(self.run_dir, None, LATENCY, conversations or self.answer, LIBRARY, echo=lambda _: None,
                     app_modes=app_modes or {})
        with captured_events() as events:
            code = run_targets(base, roots, device, reuse)
        return code, events

    def calls(self, root):
        return model_calls(self.run_dir, "select", path_id(root))


@pytest.fixture
def base(run, tmp_path_factory):  # noqa: F811
    return Base(run, tmp_path_factory.mktemp("targets"))


def apps(events):
    """Each app's end: its id, outcome and, for a stop, its code."""
    return [(e.app, e.outcome, e.data.get("code") if e.outcome == "stop" else None) for e in events
            if (e.stage, e.step, e.event) == ("guide", "target", "end")]


def last_apps(results):
    """The apps the last guide run on the only device folder under results ended."""
    [log] = results.glob("*/log/events.jsonl")
    events = [json.loads(e) for e in log.read_text().splitlines()]
    return [e["app"] for e in events if e["run"] == events[-1]["run"] and (e["stage"], e["step"], e["event"]) == ("guide", "target", "end")]


def steps(events):
    return [step for step, _, _ in guide_ends(events)]


def test_every_app_reaches_its_last_step_and_the_device_stage_runs_once(base):
    roots = [base.app("a"), base.app("b")]
    code, events = base.go(roots)
    assert code == 0 and [steps(events).count(s) for s in ("prerequisites", "grouping", "harness", "summary")] == [1, 1, 2, 1]
    assert apps(events) == [(path_id(r), "ok", None) for r in roots]


def test_a_new_target_is_the_only_app_that_runs(base):
    a, b = base.app("a"), base.app("b")
    base.go([a])
    before = base.calls(a)
    code, events = base.go([a, b])
    assert code == 0 and base.calls(a) == before and base.calls(b) > 0
    assert apps(events) == [(path_id(a), "reused", None), (path_id(b), "ok", None)] and steps(events).count("harness") == 1


def test_nothing_changed_runs_no_app_and_asks_nothing(base):
    a = base.app("a")
    base.go([a])
    before = base.calls(a)
    code, events = base.go([a])
    assert code == 0 and base.calls(a) == before and apps(events) == [(path_id(a), "reused", None)]


def test_a_changed_source_runs_that_app_again_and_only_it(base):
    a, b = base.app("a"), base.app("b")
    base.go([a, b])
    source = sorted((a / "src").rglob("*.java"))[0]
    source.write_text(source.read_text() + "\n")
    _, events = base.go([a, b])
    assert apps(events) == [(path_id(a), "ok", None), (path_id(b), "reused", None)]


def test_changed_scopes_or_a_changed_scoper_run_the_app_again(base, monkeypatch):
    a = base.app("a")
    base.go([a])
    scopes = AppTree(base.run_dir, path_id(a)).scopes
    scopes.write_text(scopes.read_text() + "\n")
    _, events = base.go([a])
    assert apps(events) == [(path_id(a), "ok", None)]
    monkeypatch.setattr(finished, "scoper_version", lambda: "another scoper")
    _, events = base.go([a])
    assert apps(events) == [(path_id(a), "ok", None)]
    _, events = base.go([a])
    assert apps(events) == [(path_id(a), "reused", None)]


def test_a_changed_harness_digest_runs_the_app_again(base, monkeypatch):
    a = base.app("a")
    base.go([a])
    asked = base.calls(a)
    monkeypatch.setenv("FAKE_HARNESS", "another harness")
    _, events = base.go([a])
    assert apps(events) == [(path_id(a), "ok", None)] and base.calls(a) == asked
    _, events = base.go([a])
    assert apps(events) == [(path_id(a), "reused", None)]


def test_a_scoper_package_with_no_code_is_one_coded_error_before_any_app(base, monkeypatch):
    a = base.app("a")
    monkeypatch.setattr(finished, "SCOPER", ("app", "moved"))
    with pytest.raises(ValueError, match=r"^missing_file: .*moved holds no scoper code"):
        base.go([a])
    assert base.calls(a) == 0


def test_a_host_root_that_is_gone_is_one_coded_error_before_any_app(base, monkeypatch):
    a = base.app("a")
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(base.tmp / "gone"))
    with pytest.raises(BenchmarkRunError, match="CRYPTOBENCH_ROOT"):
        base.go([a])
    assert base.calls(a) == 0


def test_an_older_host_without_the_digest_is_one_coded_error(base, monkeypatch):
    a = base.app("a")
    monkeypatch.setattr(finished, "identify", lambda *_: {"deviceId": "d"})
    with pytest.raises(BenchmarkRunError, match="^identify_failed: pipeline --identify reports no harness digest"):
        base.go([a])


def test_an_explicit_app_runs_even_when_nothing_changed(base):
    a = base.app("a")
    base.go([a])
    _, events = base.go([a], reuse=False)
    assert apps(events) == [(path_id(a), "ok", None)] and "harness" in steps(events)


def test_a_missing_target_says_why_and_the_others_go_on_and_its_results_stay(base):
    a, b = base.app("a"), base.app("b")
    base.go([b])
    shutil.rmtree(b)
    kept = AppTree(base.run_dir, path_id(b)).dossiers
    assert kept.is_file()
    code, events = base.go([b, a])
    assert code == 1 and kept.is_file()
    assert apps(events) == [(path_id(b), "stop", "target_missing"), (path_id(a), "ok", None)]


def test_a_stop_code_is_recorded_and_the_loop_continues(base):
    a, b = base.app("a"), base.app("b")
    code, events = base.go([a, b], conversations=dry_run())
    assert code == 1 and [o for _, *o in apps(events)] == [["stop", "no_replacement"]] * 2
    # a terminal stop is done: the rerun repeats no static step and exits 0
    assert read_json(AppTree(base.run_dir, path_id(a)).finished)["outcome"] == "no_replacement"
    code, events = base.go([a, b], conversations=dry_run())
    assert code == 0 and apps(events) == [(path_id(r), "reused", None) for r in (a, b)]


def test_a_gate_rejection_is_recorded_and_the_loop_continues(base, monkeypatch):
    a, b = base.app("a"), base.app("b")
    real = guide_steps.repair_main
    monkeypatch.setattr(guide_steps, "repair_main", lambda argv: 1 if str(a) in argv else real(argv))
    code, events = base.go([a, b])
    assert code == 1 and apps(events) == [(path_id(a), "stop", "edit_invalid"), (path_id(b), "ok", None)]


def test_a_bug_in_one_app_is_logged_and_the_others_go_on(base, monkeypatch, capsys):
    a, b = base.app("a"), base.app("b")
    real = guide_steps.dossier

    def buggy(device, app_id, *rest, **kw):
        if app_id == path_id(a):
            raise TypeError("a bug")
        return real(device, app_id, *rest, **kw)

    monkeypatch.setattr(guide_steps, "dossier", buggy)
    code, events = base.go([a, b])
    assert code == 1 and apps(events) == [(path_id(a), "stop", "bug"), (path_id(b), "ok", None)]
    assert "error bug: TypeError: a bug" in capsys.readouterr().err


def test_a_provider_failure_stops_the_whole_loop(base):
    a, b, c = base.app("a"), base.app("b"), base.app("c")

    class Failing:
        def start(self, *_):
            raise ClaudeCliError("usage limit reached")

    code, events = base.go([a, b, c], conversations=Failing())
    assert code == 1
    assert apps(events) == [(path_id(a), "stop", "replace_failed"), (path_id(b), "not_run", None), (path_id(c), "not_run", None)]
    assert not list(AppTree(base.run_dir, path_id(b)).root.glob("*"))


def test_a_device_stage_stop_runs_no_app(tmp_path):
    g = Guide(tmp_path, None, LATENCY, dry_run(), LIBRARY, echo=lambda _: None)
    with captured_events() as events:
        assert run_targets(g, [APP], False, True) == 1
    assert guide_ends(events) == [("prerequisites", "stop", "missing_results")]


def test_measured_apps_end_in_a_summary_across_them_and_are_reused(base, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(FAKE_ROOT))
    a, b = base.app("a"), base.app("b")
    code, events = base.go([a, b], device=True)
    assert code == 0
    assert set(read_json(base.run_dir / "summary.json")["apps"]) == {path_id(a), path_id(b)}
    monkeypatch.setenv("FAKE_EXIT", "3")
    code, events = base.go([a, b], device=True)
    assert code == 0 and apps(events) == [(path_id(a), "reused", None), (path_id(b), "reused", None)]


def test_a_dry_record_does_not_answer_for_a_measured_run(base, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(FAKE_ROOT))
    a = base.app("a")
    base.go([a])
    code, events = base.go([a], device=True)
    assert code == 0 and "report" in steps(events)


def settings(tmp_path, **apps):
    path = tmp_path / "perfrepair.yaml"
    path.write_text(yaml.safe_dump({"apps": apps}))
    return path


def command(device, config):
    return ["--device-results", str(device), "--agent", "dry-run", "--perfrepair-config", str(config)]


def test_no_app_and_no_targets_is_a_usage_error(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        guide_main(command(tmp_path, settings(tmp_path)))
    assert e.value.code == 2 and "--app (or apps.targets in perfrepair.yaml)" in capsys.readouterr().err


def test_a_string_target_is_a_targets_file_and_a_missing_one_is_a_coded_error(tmp_path, capsys):
    assert guide_main(command(tmp_path, settings(tmp_path, targets="one"))) == 1
    assert f"error missing_file: apps.targets file {tmp_path.resolve() / 'one'}" in capsys.readouterr().err


def test_targets_take_a_bare_string_or_a_path_and_app_narrows_to_one(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(F / "device"))
    shutil.copytree(APP, tmp_path / "rel")
    absolute = tmp_path / "abs"
    shutil.copytree(APP, absolute)
    # the same applicationId twice would merge them into one target
    (absolute / "src" / "main" / "AndroidManifest.xml").write_text('<manifest package="other" />')
    config = settings(tmp_path, targets=["rel", {"path": str(absolute)}, "rel"])
    results = tmp_path / "results"
    text = yaml.safe_load(config.read_text())
    global_yaml = tmp_path / "global.yaml"
    global_yaml.write_text("schemaVersion: 1\nselection: {testSet: x.yaml}\nproviders: {bundled: []}\n")
    text["apps"]["perfMode"] = ["latency", "throughput"]
    config.write_text(yaml.safe_dump(text))
    args = ["--agent", "dry-run", "--perfrepair-config", str(config), "--results-root", str(results), "--config", str(global_yaml)]
    assert guide_main(args) == 1
    assert sorted(last_apps(results)) == sorted([path_id(tmp_path / "rel"), path_id(absolute)])
    # a probe, then the benchmark: neither folder is a project, so the base selection
    assert len((results / "runs.log").read_text().splitlines()) == 2
    assert guide_main(["--app", str(absolute), *args]) == 1
    assert last_apps(results) == [path_id(absolute)]


def test_a_folder_that_is_no_project_says_why_in_its_line(base):
    empty = base.tmp / "empty"
    empty.mkdir()
    code, events = base.go([empty])
    assert code == 1 and apps(events) == [(path_id(empty), "stop", "app_failed")]


def test_a_path_that_is_a_file_is_a_missing_target(base):
    path = base.tmp / "a-file"
    path.write_text("x")
    code, events = base.go([Path(path)])
    assert code == 1 and apps(events)[0][1:] == ("stop", "target_missing")


def test_a_target_with_its_own_perf_mode_uses_it_in_its_dossier_and_its_record(base):
    a, b = base.app("a"), base.app("b")
    code, _ = base.go([a, b], app_modes={b: mode_of(PerfMode.parse(["throughput"]))})
    assert code == 0
    of = {r: AppTree(base.run_dir, path_id(r)) for r in (a, b)}
    assert read_json(of[a].dossiers)["perfMode"] == ["latency"] and read_json(of[b].dossiers)["perfMode"] == ["throughput"]
    assert read_json(of[a].finished)["inputs"]["perfMode"] == "latency"
    assert read_json(of[b].finished)["inputs"]["perfMode"] == "throughput"


def test_the_benchmark_must_measure_every_targets_selection():
    a, b = Path("/a"), Path("/b")
    g = Guide(None, None, LATENCY, None, LIBRARY, targets=(a, b), app_modes={b: mode_of(PerfMode.parse(["memAlloc"]))})
    assert measured_by_targets(g).keys == ("latency", "memAlloc")
    assert measured_by_targets(Guide(None, None, LATENCY, None, LIBRARY, targets=(a,))).keys == ("latency",)


@pytest.mark.parametrize("entry,want", [("x", None), ({"path": "x"}, None), ({"path": "x", "perfMode": "all"}, "generic"),
                                        ({"path": "x", "perfMode": ["energy"]}, "energy")])
def test_a_target_entry_reads_its_own_perf_mode(entry, want):
    got = target_perf(entry)
    assert target_path(entry) == "x" and (got.name if got else None) == want


def test_a_bad_target_perf_mode_warns_like_any_bad_targets(tmp_path, capsys):
    with pytest.raises(SystemExit):
        guide_main(command(tmp_path, settings(tmp_path, targets=[{"path": "x", "perfMode": "fast"}])))
    assert "invalid: apps.targets" in capsys.readouterr().err


def test_no_entry_that_is_an_app_stops_before_any_device_step(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(F / "device"))
    (tmp_path / "readme").mkdir()
    (tmp_path / "readme" / "README.md").write_text("x")
    config = settings(tmp_path, targets=["readme", {"root": "readme"}])
    assert guide_main(["--agent", "dry-run", "--perfrepair-config", str(config), "--results-root", str(tmp_path / "results")]) == 1
    assert "error no_targets: " in capsys.readouterr().err
    assert not (tmp_path / "results").exists()


def test_targets_yaml_is_written_and_a_path_entry_that_is_no_app_is_its_stop(base):
    a = base.app("a")
    readme = base.tmp / "readme"
    readme.mkdir()
    found = resolve_targets([str(a), str(readme)], base.tmp / "perfrepair.yaml")
    g = Guide(base.run_dir, None, LATENCY, base.answer, LIBRARY, echo=lambda _: None, target_set=found)
    with captured_events() as events:
        assert run_targets(g, [t.path for t in found.apps], False, True) == 1
    assert apps(events) == [(path_id(readme), "stop", "not_android_project"), (path_id(a), "ok", None)]
    doc = yaml.safe_load((base.run_dir / "targets.yaml").read_text())
    assert doc == found.document() and doc["skipped"][0]["entry"] == {"path": str(readme)}
