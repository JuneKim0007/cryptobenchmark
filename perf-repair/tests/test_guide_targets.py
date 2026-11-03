"""The guide over apps.targets: the device stage once, each app isolated, a line per app, reuse by inputs; scripted model, no device."""
import shutil
from pathlib import Path

import pytest
import yaml
from helpers import LIBRARY
from test_guide import APP, F, FAKE_ROOT, replacing
from test_stages import run  # noqa: F401  the recorded run, grouped

from perfrepair import failure
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.runtime.gateway.claude_cli import ClaudeCliError
from perfrepair.ai.suggest.site_replace.command import DRY_RUN
from perfrepair.app.facts.path_id import path_id
from perfrepair.files import read_json
from perfrepair.guide import finished, steps as guide_steps
from perfrepair.guide.command import main as guide_main
from perfrepair.guide.steps import Guide
from perfrepair.guide.targets import run_targets
from perfrepair.log import attach
from perfrepair.log.read import read_events
from perfrepair.result.modes import MODES
from perfrepair.run_dir import EVENTS, AppPaths


class Base:
    def __init__(self, run_dir, tmp_path):
        self.run_dir, self.tmp = run_dir, tmp_path
        self.answer = ScriptedConversations(self._first_option)

    def _first_option(self, task, *_):
        # the dossier of the app being asked: the newest written
        newest = max(self.run_dir.glob("*/dossiers.json"), key=lambda p: p.stat().st_mtime_ns)
        return replacing(read_json(newest), task)[0]

    def app(self, name):
        path = self.tmp / "apps" / name
        if not path.exists():
            shutil.copytree(APP, path)
        return path.resolve()

    def go(self, roots, device=False, reuse=True, conversations=None):
        lines = []
        base = Guide(self.run_dir, None, MODES["latency"], conversations or self.answer, LIBRARY, echo=lines.append)
        return run_targets(base, roots, device, reuse), lines

    def calls(self, root):
        journal = AppPaths(self.run_dir, path_id(root)).replace / "journal.jsonl"
        return len(journal.read_text().splitlines()) if journal.is_file() else 0


@pytest.fixture
def base(run, tmp_path_factory):  # noqa: F811
    return Base(run, tmp_path_factory.mktemp("targets"))


def app_lines(lines):
    return [line for line in lines if line.startswith("app ")]


def test_every_app_reaches_its_last_step_and_the_device_stage_runs_once(base):
    roots = [base.app("a"), base.app("b")]
    code, lines = base.go(roots)
    assert code == 0
    assert sum(line.startswith("guide prerequisites:") for line in lines) == 1
    assert sum(line.startswith("guide grouping:") for line in lines) == 1
    assert sum(line.startswith("guide harness:") for line in lines) == 2
    assert app_lines(lines) == [f"app {path_id(r)}: ok" for r in roots]
    assert lines[-3] == "guide summary: ok: no app has a report yet"


def test_a_new_target_is_the_only_app_that_runs(base):
    a, b = base.app("a"), base.app("b")
    base.go([a])
    before = base.calls(a)
    code, lines = base.go([a, b])
    assert code == 0 and base.calls(a) == before and base.calls(b) > 0
    assert app_lines(lines) == [f"app {path_id(a)}: reused", f"app {path_id(b)}: ok"]
    assert sum(line.startswith("guide harness:") for line in lines) == 1


def test_nothing_changed_runs_no_app_and_asks_nothing(base):
    a = base.app("a")
    base.go([a])
    before = base.calls(a)
    code, lines = base.go([a])
    assert code == 0 and base.calls(a) == before and app_lines(lines) == [f"app {path_id(a)}: reused"]


def test_a_changed_source_runs_that_app_again_and_only_it(base):
    a, b = base.app("a"), base.app("b")
    base.go([a, b])
    source = sorted((a / "src").rglob("*.java"))[0]
    source.write_text(source.read_text() + "\n")
    _, lines = base.go([a, b])
    assert app_lines(lines)[0] == f"app {path_id(a)}: ok" and app_lines(lines)[1] == f"app {path_id(b)}: reused"


def test_changed_scopes_or_a_changed_scoper_run_the_app_again(base, monkeypatch):
    a = base.app("a")
    base.go([a])
    scopes = AppPaths(base.run_dir, path_id(a)).scopes
    scopes.write_text(scopes.read_text() + "\n")
    _, lines = base.go([a])
    assert app_lines(lines) == [f"app {path_id(a)}: ok"]
    monkeypatch.setattr(finished, "scoper_version", lambda: "another scoper")
    _, lines = base.go([a])
    assert app_lines(lines) == [f"app {path_id(a)}: ok"]
    _, lines = base.go([a])
    assert app_lines(lines) == [f"app {path_id(a)}: reused"]


def test_an_explicit_app_runs_even_when_nothing_changed(base):
    a = base.app("a")
    base.go([a])
    _, lines = base.go([a], reuse=False)
    assert app_lines(lines) == [f"app {path_id(a)}: ok"] and any(line.startswith("guide harness:") for line in lines)


def test_a_capped_app_is_never_reused(base):
    a = base.app("a")
    lines = []
    capped = Guide(base.run_dir, None, MODES["latency"], base.answer, LIBRARY, echo=lines.append, limit=1)
    run_targets(capped, [a], False, True)
    lines.clear()
    run_targets(capped, [a], False, True)
    assert app_lines(lines) != [f"app {path_id(a)}: reused"]


def test_a_missing_target_says_why_and_the_others_go_on_and_its_results_stay(base):
    a, b = base.app("a"), base.app("b")
    base.go([b])
    shutil.rmtree(b)
    kept = AppPaths(base.run_dir, path_id(b)).dossiers
    assert kept.is_file()
    code, lines = base.go([b, a])
    assert code == 1 and kept.is_file()
    assert app_lines(lines)[0] == f"app {path_id(b)}: stop target_missing: {b} is no folder; its earlier results stay"
    assert app_lines(lines)[1] == f"app {path_id(a)}: ok"


def test_a_stop_code_is_recorded_and_the_loop_continues(base):
    a, b = base.app("a"), base.app("b")
    code, lines = base.go([a, b], conversations=DRY_RUN)
    assert code == 1
    assert [line.split(":")[1].split()[:2] for line in app_lines(lines)] == [["stop", "no_replacement"]] * 2
    assert not AppPaths(base.run_dir, path_id(a)).finished.exists()


def test_a_gate_rejection_is_recorded_and_the_loop_continues(base, monkeypatch):
    a, b = base.app("a"), base.app("b")
    real = guide_steps.repair_main
    monkeypatch.setattr(guide_steps, "repair_main", lambda argv: 1 if str(a) in argv else real(argv))
    code, lines = base.go([a, b])
    assert code == 1 and "stop edit_invalid at edit" in app_lines(lines)[0] and app_lines(lines)[1].endswith(": ok")


def test_a_bug_in_one_app_is_logged_and_the_others_go_on(base, monkeypatch, capsys):
    a, b = base.app("a"), base.app("b")
    real = guide_steps.dossier

    def buggy(device, app_id, *rest, **kw):
        if app_id == path_id(a):
            raise TypeError("a bug")
        return real(device, app_id, *rest, **kw)

    monkeypatch.setattr(guide_steps, "dossier", buggy)
    code, lines = base.go([a, b])
    assert code == 1 and "stop bug at app: TypeError: a bug" in app_lines(lines)[0] and app_lines(lines)[1].endswith(": ok")
    assert "error bug: TypeError: a bug" in capsys.readouterr().err


def test_a_provider_failure_stops_the_whole_loop(base):
    a, b, c = base.app("a"), base.app("b"), base.app("c")

    class Failing:
        def start(self, *_):
            raise ClaudeCliError("usage limit reached")

    code, lines = base.go([a, b, c], conversations=Failing())
    assert code == 1
    first, second, third = app_lines(lines)
    assert "stop replace_failed at replace: claude_cli_failed: usage limit reached" in first
    assert f"app {path_id(b)}: not_run {path_id(a)} hit a provider failure" in second and "not_run" in third
    assert not list(AppPaths(base.run_dir, path_id(b)).root.glob("*"))


def test_a_device_stage_stop_runs_no_app(tmp_path):
    lines = []
    g = Guide(tmp_path, None, MODES["latency"], DRY_RUN, LIBRARY, echo=lines.append)
    assert run_targets(g, [APP], False, True) == 1
    assert len(lines) == 1 and lines[0].startswith("guide prerequisites: stop missing_results")


def test_measured_apps_end_in_a_summary_across_them_and_are_reused(base, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(FAKE_ROOT))
    a, b = base.app("a"), base.app("b")
    code, lines = base.go([a, b], device=True)
    assert code == 0 and any(line.startswith("guide summary: ok: ") and "2 apps" in line for line in lines)
    assert set(read_json(base.run_dir / "summary.json")["apps"]) == {path_id(a), path_id(b)}
    monkeypatch.setenv("FAKE_EXIT", "3")
    code, lines = base.go([a, b], device=True)
    assert code == 0 and app_lines(lines) == [f"app {path_id(a)}: reused", f"app {path_id(b)}: reused"]


def test_a_dry_record_does_not_answer_for_a_measured_run(base, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(FAKE_ROOT))
    a = base.app("a")
    base.go([a])
    code, lines = base.go([a], device=True)
    assert code == 0 and any(line.startswith("guide report:") for line in lines)


def test_each_app_logs_with_its_app_set(base):
    a, b = base.app("a"), base.app("b")

    def body():
        attach(base.run_dir)
        return base.go([a, b])[0]

    attach()
    assert failure.reported(body) == 0
    events = [e for e in read_events(base.run_dir / EVENTS) if e.stage == "guide"]
    for root in (a, b):
        assert {e.step for e in events if e.app == path_id(root)} >= {"app", "dossier", "replace", "edit", "harness", "target"}
    assert {e.step for e in events if e.app is None} >= {"prerequisites", "grouping", "summary"}


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


def test_malformed_targets_warn_then_count_as_none(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        guide_main(command(tmp_path, settings(tmp_path, targets="one")))
    err = capsys.readouterr().err
    assert e.value.code == 2 and "invalid: apps.targets one, a list of paths or {path: ...}; ignored" in err


def test_targets_take_a_bare_string_or_a_path_and_app_narrows_to_one(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(F / "device"))
    (tmp_path / "rel").mkdir()
    absolute = tmp_path / "abs"
    absolute.mkdir()
    config = settings(tmp_path, targets=["rel", {"path": str(absolute)}, "rel"])
    results = tmp_path / "results"
    text = yaml.safe_load(config.read_text())
    global_yaml = tmp_path / "global.yaml"
    global_yaml.write_text("schemaVersion: 1\nselection: {testSet: x.yaml}\nproviders: {bundled: []}\n")
    text.update(paths={"results": str(results)}, device={"benchmark": {"config": str(global_yaml)}})
    config.write_text(yaml.safe_dump(text))
    args = ["--agent", "dry-run", "--perfrepair-config", str(config)]
    assert guide_main(args) == 1
    out = capsys.readouterr().out
    assert len(app_lines(out.splitlines())) == 2 and f"app {path_id(tmp_path / 'rel')}:" in out
    assert len((results / "runs.log").read_text().splitlines()) == 1
    assert guide_main(["--app", str(absolute), *args]) == 1
    out = capsys.readouterr().out
    assert [line.split(":")[0] for line in app_lines(out.splitlines())] == [f"app {path_id(absolute)}"]


def test_a_folder_that_is_no_project_says_why_in_its_line(base):
    empty = base.tmp / "empty"
    empty.mkdir()
    code, lines = base.go([empty])
    assert code == 1 and "stop app_failed at app: not_android_project: " in app_lines(lines)[0]


def test_a_path_that_is_a_file_is_a_missing_target(base):
    path = base.tmp / "a-file"
    path.write_text("x")
    code, lines = base.go([Path(path)])
    assert code == 1 and "target_missing" in app_lines(lines)[0]
