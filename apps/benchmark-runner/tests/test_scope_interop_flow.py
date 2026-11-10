"""A --harness run on a fake phone: the scope check in its own process, its verdicts in the plan, and nothing timed."""
import pathlib, types

import pytest
import yaml

from stages import harness  # noqa: E402
from fake_phone import Phone  # noqa: E402


def test_the_scope_check_is_its_own_process(tmp_path):
    phone = Phone(tmp_path)
    interop = phone.check_scopes(tmp_path / "scoped")
    assert phone.log == ["clear", "instrument ScopedInterop", "pull scoped-interop.yaml"] and interop.name == "scoped-interop.yaml"


def test_a_harness_run_writes_the_verdicts_into_the_plan_and_times_nothing(tmp_path, monkeypatch):
    phone, scoped = Phone(tmp_path), tmp_path / "scoped"
    scoped.mkdir()
    plan = scoped / "scoped-plan.yaml"
    plan.write_text(yaml.safe_dump({"scopes": [{"id": "a", "status": "compiled", "interop": {"check": "same_output"}}]}))
    capture = tmp_path / "capture"
    monkeypatch.setattr(harness, "discover", lambda *_arguments: (tmp_path, tmp_path / "effective", capture, tmp_path / "trial", {}))
    monkeypatch.setattr(harness, "require_harness_device", lambda *_arguments: None)
    pushed = []
    monkeypatch.setattr(harness, "push", lambda _device, _options, files: pushed.extend(files))
    monkeypatch.setattr(phone, "pull", lambda _remote, local: pathlib.Path(local).write_text('"a": {interop: passed, check: same_output}\n'))
    files = harness.check_scopes(types.SimpleNamespace(harness=str(tmp_path / "harness.yaml")), None, phone, tmp_path, scoped, plan)
    assert capture in pushed and phone.ran == [] and files["scopedPlan"] == plan
    record = yaml.safe_load(plan.read_text())["scopes"][0]
    assert (record["status"], record["interop"]["result"]) == ("checked", "passed")


def test_a_failed_generate_leaves_the_plan_its_failure_line_names(tmp_path, monkeypatch, capsys):
    def generate(_harness, _root, out):
        out.mkdir(parents=True, exist_ok=True)
        (out / "scoped-plan.yaml").write_text("scopes: []\n")
        return out / "scoped-plan.yaml", []
    monkeypatch.setattr(harness.scope_generate, "generate", generate)
    monkeypatch.setattr(harness.scope_generate, "clean", lambda _root: None)
    results = tmp_path / "checked"
    with pytest.raises(SystemExit) as stopped:
        harness.harness_run(types.SimpleNamespace(harness=str(tmp_path / "harness.yaml")), None, None, results)
    assert stopped.value.code == 1
    named = capsys.readouterr().err.split("see ")[-1].strip()
    assert named == str(results / harness.paths.SCOPED_PLAN_FAILED) and pathlib.Path(named).read_text() == "scopes: []\n"
    assert not (results / "scoped").exists()
