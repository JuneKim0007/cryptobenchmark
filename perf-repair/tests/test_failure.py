"""Every command reports a bad input as one `error ...` line and exit 1, never a traceback."""
from pathlib import Path

import pytest

from perfrepair.ai.__main__ import main as ai
from perfrepair.app.__main__ import main as app
from perfrepair.data_handler.inbound.__main__ import main as inbound
from perfrepair.grouping.__main__ import main as grouping
from perfrepair.guide.command import main as guide
from perfrepair.repair.__main__ import main as repair
from perfrepair.report.__main__ import main as report
from perfrepair.validation.__main__ import main as validation

F = Path(__file__).parent / "fixtures" / "results" / "manifest.yaml"


def _commands(d: Path):
    run, app_dir = str(d / "run"), str(d)
    return [
        (inbound, ["--manifest", app_dir, "-o", run]),
        (grouping, ["build", "--manifest", app_dir, "--run", run]),
        (grouping, ["assign", "--run", run, "--agent", "dry-run"]),
        (grouping, ["report", "--run", run]),
        (grouping, ["interop-plan", "--run", run]),
        (ai, ["worthiness", "--run", run, "--mode", "latency", "--agent", "dry-run"]),
        (ai, ["replace", "--run", run, "--app", "x", "--agent", "dry-run"]),
        (repair, ["dossier", "--run", run, "--app", "x", "--source", app_dir]),
        (repair, ["test-set", "--run", run, "--app", "x", "-o", str(d / "t.yaml")]),
        (repair, ["edit", "--run", run, "--app", "x", "--source", app_dir]),
        (repair, ["harness", "--run", run, "--app", "x", "--manifest", str(F)]),
        (app, ["--manifest", app_dir, "--app", app_dir, "--run", run, "--name", "x"]),
        (report, ["app", "--run", run, "--app", "x"]),
    ]


@pytest.mark.parametrize("n", range(len(_commands(Path(".")))))
def test_a_bad_input_is_one_error_line_and_exit_1(n, tmp_path, capsys):
    (tmp_path / "run").mkdir()
    command, argv = _commands(tmp_path)[n]
    assert command(argv) == 1
    err = capsys.readouterr().err
    assert "Traceback" not in err and sum(line.startswith("error ") for line in err.splitlines()) == 1, err


def test_a_malformed_rows_json_is_a_reported_problem(tmp_path, capsys):
    (tmp_path / "rows.json").write_text("{not json")
    assert validation([str(tmp_path)]) == 1
    assert capsys.readouterr().out.startswith("rows.json: 1 problem(s)\n  - does not parse: JSONDecodeError")


def _claude_missing(tmp_path) -> Path:
    config = tmp_path / "perfrepair.yaml"
    config.write_text(f"agent: {{backend: claude-code, claudeBinary: {tmp_path / 'no-claude'}}}\n")
    return config


def test_a_cli_that_cannot_run_is_claude_cli_failed_in_a_model_command(tmp_path, capsys):
    run = tmp_path / "run"
    assert inbound(["--manifest", str(F), "-o", str(run)]) == 0
    assert grouping(["build", "--manifest", str(F), "--run", str(run)]) == 0
    capsys.readouterr()
    assert grouping(["assign", "--run", str(run), "--perfrepair-config", str(_claude_missing(tmp_path))]) == 1
    assert capsys.readouterr().err.splitlines()[-1].startswith("error claude_cli_failed: cannot run ")


def test_the_guide_stops_on_claude_cli_failed(tmp_path, capsys, monkeypatch):
    from perfrepair.guide import command

    def failing(g):
        from perfrepair.ai.runtime.agent import ClaudeCodeError
        raise ClaudeCodeError("not logged in")
    monkeypatch.setattr(command, "DRY", (("dossier", failing),))
    run = tmp_path / "run"
    run.mkdir()
    assert guide(["--app", str(tmp_path), "--name", "x", "--run", str(run), "--results", str(tmp_path),
                  "--agent", "dry-run"]) == 1
    assert "guide dossier: stop dossier_failed: claude_cli_failed: not logged in" in capsys.readouterr().out
