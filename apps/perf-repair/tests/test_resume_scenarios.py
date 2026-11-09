"""The resume probe's scenarios: what a rerun reuses, repeats or refuses after a stop, a crash, a cap or a change;
scripted model, fixture apps, the fake pipeline, no device."""
import os
import subprocess
import sys

import pytest
import yaml
from helpers import LATENCY, LIBRARY, captured_events, guide_ends
from test_guide import FAKE_ROOT
from test_guide_targets import Base, apps, steps
from test_run_lock import HOLD, SRC
from test_stages import run  # noqa: F401  the recorded run, grouped

from cryptobench.paths import AppTree, RunTree
from perfrepair.ai.select.command import dry_run
from perfrepair.app.facts.path_id import path_id
from perfrepair.dto.perf_mode import PerfMode
from perfrepair.files import read_json
from perfrepair.grouping.__main__ import main as grouping
from perfrepair.guide import app_steps
from perfrepair.guide.state import Guide
from perfrepair.guide.targets import run_targets
from perfrepair.result.modes import mode_of
from perfrepair.run_dir.run_record import STOPPED

THROUGHPUT = mode_of(PerfMode.parse(["throughput"]))
OTHER = '''package demo;

import javax.crypto.Cipher;

class Other {
    byte[] wrap(byte[] in, int n) throws Exception {
        Cipher k = Cipher.getInstance("AES/GCM/NoPadding", "Slow");
        byte[] out = k.doFinal(in);
        return n > 0 ? out : in;
    }
}
'''


class Probe(Base):
    def go(self, roots, device=False, reuse=True, conversations=None, **fields):
        g = Guide(self.run_dir, None, fields.pop("mode", LATENCY), conversations or self.answer, LIBRARY, echo=lambda _: None,
                  **fields)
        with captured_events() as events:
            code = run_targets(g, roots, device, reuse)
        return code, events

    def paths(self, root):
        return AppTree(self.run_dir, path_id(root))

    def two_units(self, name):
        root = self.app(name)
        (root / "src" / "main" / "java" / "demo" / "Other.java").write_text(OTHER)
        return root

    def record(self):
        return read_json(max((RunTree(self.run_dir).runs).glob("run_*.json"), key=lambda p: p.stat().st_mtime_ns))


@pytest.fixture
def p(run, tmp_path_factory):  # noqa: F811
    return Probe(run, tmp_path_factory.mktemp("probe"))


def _no_options(monkeypatch, only=None):
    real = app_steps.dossier

    def empty(device, app_id, *rest, **kw):
        doc = real(device, app_id, *rest, **kw)
        return {**doc, "dossiers": []} if only in (None, app_id) else doc
    monkeypatch.setattr(app_steps, "dossier", empty)


def _touch(root):
    source = sorted((root / "src").rglob("*.java"))[0]
    source.write_text(source.read_text() + "\n")


@pytest.mark.parametrize("how", ["no_replacement", "no_options"])
def test_s2_a_terminal_stop_is_done_and_its_rerun_repeats_nothing(p, monkeypatch, how):
    """Before: re-run every time, exit 1. After: reused, exit 0."""
    a = p.app("a")
    if how == "no_options":
        _no_options(monkeypatch)
    code, _ = p.go([a], conversations=dry_run())
    assert code == 1 and read_json(p.paths(a).finished)["outcome"] == how
    code, events = p.go([a], conversations=dry_run())
    assert code == 0 and apps(events) == [(path_id(a), "reused", None)] and "app" not in steps(events)


def test_s3_ctrl_c_mid_app_still_writes_the_summary_and_index_then_raises(p, monkeypatch):
    """Before: summary, apps-index.tsv and the target line skipped. After: written, the app recorded stopped."""
    a, b = p.app("a"), p.app("b")
    p.go([a])
    _touch(a)
    monkeypatch.setattr(app_steps, "repair_main", lambda argv: (_ for _ in ()).throw(KeyboardInterrupt()))
    g = Guide(p.run_dir, None, LATENCY, p.answer, LIBRARY, echo=lambda _: None)
    (RunTree(p.run_dir).apps_index).unlink()
    with captured_events() as events, pytest.raises(KeyboardInterrupt):
        run_targets(g, [a, b], False, True)
    assert "summary" in steps(events) and (RunTree(p.run_dir).apps_index).is_file()
    assert [(app, outcome) for app, outcome, _ in apps(events)] == [(path_id(a), "stop")]
    assert p.record()["apps"][path_id(a)] == {"status": STOPPED, "step": "edit", "reason": "interrupted"}
    assert not p.paths(a).finished.exists()
    monkeypatch.undo()
    before = p.calls(a)
    code, events = p.go([a, b])
    assert code == 0 and apps(events)[0] == (path_id(a), "ok", None) and p.calls(a) == before


def test_s4_the_summary_holds_no_report_of_an_app_that_stopped_on_the_latest_run(p, monkeypatch):
    """Before: a's stale report.json stayed in summary.json. After: cleared on its rerun's first step."""
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(FAKE_ROOT))
    a, b = p.app("a"), p.app("b")
    p.go([a, b], device=True)
    assert set(read_json(RunTree(p.run_dir).summary)["apps"]) == {path_id(a), path_id(b)}
    _touch(a)
    _no_options(monkeypatch, path_id(a))
    p.go([a, b], device=True)
    assert not p.paths(a).report.exists() and list(read_json(RunTree(p.run_dir).summary)["apps"]) == [path_id(b)]


def test_s5_another_harness_config_is_another_measurement(p, monkeypatch, tmp_path):
    """Before: a changed --harness-config reused the old measurement. After: the app measures again."""
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(FAKE_ROOT))
    a = p.app("a")
    p.go([a], device=True)
    other = tmp_path / "other-global.yaml"
    other.write_text(yaml.safe_dump({"schemaVersion": 1, "providers": {"bundled": []}}))
    code, events = p.go([a], device=True, app_config=other)
    assert code == 0 and apps(events) == [(path_id(a), "ok", None)] and "device" in steps(events)
    assert apps(p.go([a], device=True, app_config=other)[1]) == [(path_id(a), "reused", None)]


def test_s5_refresh_runs_a_done_app(p):
    """Before: --refresh was a no-op for a finished app. After: refresh implies no reuse."""
    a = p.app("a")
    p.go([a])
    _, events = p.go([a], refresh=True)
    assert apps(events) == [(path_id(a), "ok", None)]


def test_s6_a_cap_that_left_units_unasked_is_not_done(p):
    """Before: the capped run was recorded finished and an uncapped rerun asked nothing. After: the rest are asked."""
    a = p.two_units("a")
    p.go([a], limit=1)
    assert p.calls(a) == 1 and not p.paths(a).finished.exists()
    assert p.record()["apps"][path_id(a)]["reason"] == "apps.limit left 1 scopes unasked"
    code, events = p.go([a])
    assert code == 0 and apps(events) == [(path_id(a), "ok", None)] and p.calls(a) == 2
    assert apps(p.go([a])[1]) == [(path_id(a), "reused", None)]


def test_s6_a_cap_that_asked_every_unit_is_done(p):
    """Before: any cap ran the static steps every time. After: a cap that left nothing is reused."""
    a = p.app("a")
    p.go([a], limit=5)
    assert apps(p.go([a], limit=5)[1]) == [(path_id(a), "reused", None)]


def test_s6_aba_a_stopped_rerun_leaves_no_done_mark_to_revert_onto(p):
    """Before: run 3 (latency again) reused run 1's mark beside run 2's throughput dossiers. After: it runs."""
    a = p.app("a")
    p.go([a])
    code, _ = p.go([a], conversations=dry_run(), mode=THROUGHPUT)
    # Select asks the changed units again, keeps them all, and no_replacement is terminal: the mark is run 2's
    assert code == 1 and read_json(p.paths(a).finished)["inputs"]["perfMode"] == THROUGHPUT.name
    code, events = p.go([a])
    assert apps(events)[0][0] == path_id(a) and apps(events)[0][1] != "reused"
    assert read_json(p.paths(a).dossiers)["perfMode"] == ["latency"]


@pytest.mark.parametrize("content", ["", '{"tree": ', "[]", "null"])
def test_s9_a_corrupt_done_mark_reruns_the_app_and_heals(p, content):
    """Before: '' or a cut file was `stop bug at app` on every run. After: rerun once, then reused."""
    a = p.app("a")
    p.go([a])
    p.paths(a).finished.write_text(content)
    code, events = p.go([a])
    assert code == 0 and apps(events) == [(path_id(a), "ok", None)]
    assert apps(p.go([a])[1]) == [(path_id(a), "reused", None)]


def test_s7_a_folder_an_interrupted_benchmark_left_is_refused_by_a_standalone_command(p, tmp_path, capsys):
    """Before: its 14 older files were read as current. After: not_device_results."""
    left = tmp_path / "left"
    left.mkdir()
    (RunTree(left).rows).write_text((RunTree(p.run_dir).rows).read_text())
    assert grouping(["build", "--device-results", str(left)]) == 1
    assert capsys.readouterr().err.splitlines()[-1].startswith("error not_device_results: ")


def test_s8_a_second_guide_on_the_folder_is_device_busy(p):
    """Before: two guides raced (4 of 12 runs failed on a shared temp file). After: the second stops at once."""
    holder = subprocess.Popen([sys.executable, "-c", HOLD, str(p.run_dir)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              text=True, env={**os.environ, "PYTHONPATH": os.pathsep.join([str(SRC), str(SRC.parents[2] / "lib/cryptobench")])})
    try:
        assert holder.stdout.readline().strip() == "held"
        code, events = p.go([p.app("a")])
    finally:
        holder.stdin.close()
        holder.wait(10)
    assert code == 1 and guide_ends(events)[-1] == ("prerequisites", "stop", "device_busy")


@pytest.mark.parametrize("on_existing, line", [("overwrite", "ok"), ("resume", "reused")])
def test_a_named_run_id_that_exists_follows_on_existing(p, on_existing, line):
    a = p.app("a")
    p.go([a], run_id="r1")
    assert apps(p.go([a], run_id="r1", on_existing=on_existing)[1]) == [(path_id(a), line, None)]


def test_skip_runs_nothing(p):
    a = p.app("a")
    p.go([a], run_id="r1")
    code, events = p.go([a], run_id="r1", on_existing="skip")
    assert code == 1 and [end[1:] for end in guide_ends(events)] == [("stop", "run_exists")]


def test_an_app_run_removes_an_earlier_targets_file(p):
    (RunTree(p.run_dir).targets).write_text("apps: []\n")
    p.go([p.app("a")], reuse=False)
    assert not (RunTree(p.run_dir).targets).exists()
