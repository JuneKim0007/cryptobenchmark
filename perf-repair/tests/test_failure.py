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
from helpers import with_results

F = Path(__file__).parent / "fixtures" / "results" / "test-api36-00000000" / "manifest.yaml"


def _commands(d: Path):
    run, app_dir = str(d / "run"), str(d)
    return [
        (inbound, ["--device-results", run]),
        (grouping, ["build", "--device-results", run]),
        (grouping, ["assign", "--device-results", run, "--agent", "dry-run"]),
        (grouping, ["report", "--device-results", run]),
        (grouping, ["interop-plan", "--device-results", run]),
        (ai, ["worthiness", "--device-results", run, "--perf-mode", "latency", "--agent", "dry-run"]),
        (ai, ["replace", "--device-results", run, "--app", "x", "--agent", "dry-run"]),
        (repair, ["dossier", "--device-results", run, "--app", app_dir]),
        (repair, ["test-set", "--device-results", run, "--app", "x", "-o", str(d / "t.yaml")]),
        (repair, ["edit", "--device-results", run, "--app", app_dir]),
        (repair, ["harness", "--device-results", run, "--app", "x"]),
        (app, ["--device-results", run, "--app", app_dir]),
        (report, ["app", "--device-results", run, "--app", "x"]),
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
    assert validation(["--device-results", str(tmp_path)]) == 1
    assert capsys.readouterr().out.startswith("rows.json: 1 problem(s)\n  - does not parse: JSONDecodeError")


def _claude_missing(tmp_path) -> Path:
    config = tmp_path / "perfrepair.yaml"
    config.write_text(f"aiGateway: {{use: claude, claude: {{auth: subscription, binary: {tmp_path / 'no-claude'}}}}}\n")
    return config


@pytest.mark.usefixtures("asked_by_model")
def test_a_cli_that_cannot_run_is_claude_cli_failed_in_a_model_command(tmp_path, capsys):
    run = tmp_path / "run"
    assert inbound(["--device-results", str(with_results(run))]) == 0
    assert grouping(["build", "--device-results", str(with_results(run))]) == 0
    capsys.readouterr()
    assert grouping(["assign", "--device-results", str(run), "--perfrepair-config", str(_claude_missing(tmp_path))]) == 1
    assert capsys.readouterr().err.splitlines()[-1].startswith("error claude_cli_failed: cannot run ")


def test_the_guide_stops_on_claude_cli_failed(tmp_path, capsys, monkeypatch):
    from perfrepair.guide import targets

    def failing(g):
        from perfrepair.ai.runtime.gateway.claude_cli import ClaudeCliError
        raise ClaudeCliError("not logged in")
    monkeypatch.setattr(targets, "DEVICE_LEVEL", (("dossier", failing),))
    run = tmp_path / "run"
    run.mkdir()
    assert guide(["--app", str(tmp_path), "--device-results", str(run),
                  "--agent", "dry-run"]) == 1
    assert "guide dossier: stop dossier_failed: claude_cli_failed: not logged in" in capsys.readouterr().out
