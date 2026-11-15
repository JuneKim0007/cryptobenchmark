"""A failed analysis script is one warning, and the run keeps the files it measured."""
from cryptobench.stages.analysis import scripts


def test_a_failed_chart_script_is_a_warning_and_analysis_goes_on(tmp_path, monkeypatch, capsys):
    tools = tmp_path / "apps/benchmark-runner/analysis"
    tools.mkdir(parents=True)
    (tools / "analyze.py").write_text("import no_such_module_at_all\n")
    (tools / "charts.py").write_text("raise SystemExit('never reached')\n")
    monkeypatch.setattr(scripts.paths, "repo", lambda: scripts.paths.Repo(tmp_path))
    files = {}
    scripts.analyse(tmp_path, files, tmp_path / "effective.yaml", tmp_path / "preparation", tmp_path / "benchmark", [], 1)
    out = capsys.readouterr().out
    assert out.count("charts_failed") == 1
    assert files["benchmark"] == tmp_path / "benchmark/benchmark.json"
