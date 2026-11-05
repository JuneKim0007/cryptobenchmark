import argparse
import ast
import pathlib
import subprocess
import sys

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import dependencies
from stages import benchmark

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCANNED = ("apps/benchmark-runner", "apps/cli", "tools", "apps/perf-repair/src")
# import name to the name requirements.txt installs it under
INSTALLED_AS = {"yaml": "pyyaml", "tree_sitter": "tree-sitter", "tree_sitter_java": "tree-sitter-java",
                "tree_sitter_kotlin": "tree-sitter-kotlin"}
THIRD_PARTY = {"yaml", "matplotlib", "perfetto", "manafa", "anthropic", "tree_sitter", "tree_sitter_java", "tree_sitter_kotlin"}


def requirements():
    lines = [line.strip() for line in (ROOT / "requirements.txt").read_text().splitlines()]
    return [line for line in lines if line and not line.startswith("#")]


def installed():
    return {line.split("=")[0].split(">")[0].lower() for line in requirements()}


def imported_top_levels(path):
    found = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            found |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module.split(".")[0])
    return found


def test_every_third_party_module_the_repo_imports_is_in_requirements():
    imported = set()
    for folder in SCANNED:
        for path in (ROOT / folder).rglob("*.py"):
            if "/tests/" not in path.as_posix():
                imported |= imported_top_levels(path)
    # a module neither stdlib nor the repo's own would be missing from THIRD_PARTY, or from the file
    names = imported - set(sys.stdlib_module_names)
    own = {p.stem for folder in SCANNED for p in (ROOT / folder).rglob("*.py")} | {p.name for folder in SCANNED for p in (ROOT / folder).rglob("*") if p.is_dir()}
    assert names - own - THIRD_PARTY == set()
    assert {INSTALLED_AS.get(m, m) for m in THIRD_PARTY} <= installed()


def test_the_scope_pins_are_the_ones_pyproject_names():
    pyproject = (ROOT / "apps/perf-repair/pyproject.toml").read_text()
    for pin in ("tree-sitter==", "tree-sitter-java==", "tree-sitter-kotlin=="):
        line = next(r for r in requirements() if r.startswith(pin))
        assert f'"{line}"' in pyproject


def options(**set_):
    defaults = {"probe": False, "identify": False, "interop": None, "harness": None, "bench": False, "device": False,
                "energy_python": sys.executable}
    return argparse.Namespace(**{**defaults, **set_})


@pytest.fixture
def config(tmp_path):
    def write(run):
        path = tmp_path / "global.yaml"
        path.write_text(yaml.safe_dump({"run": run}))
        return path
    return write


@pytest.fixture
def hidden(monkeypatch):
    """The module names find_spec answers None for; every other is present."""
    names = set()
    monkeypatch.setattr(dependencies.importlib.util, "find_spec", lambda module: None if module in names else object())
    return names


def test_a_bench_without_matplotlib_is_one_coded_line_and_exit_1(config, hidden, capsys):
    hidden.add("matplotlib")
    with pytest.raises(SystemExit) as stopped:
        dependencies.check(options(bench=True), config({}))
    assert stopped.value.code == 1
    assert "missing_dependency: matplotlib" in capsys.readouterr().err


@pytest.mark.parametrize("asked", [{"probe": True}, {"identify": True}, {"interop": "plan.yaml", "bench": True}, {},
                                   {"device": True, "harness": "harness.yaml"}])
def test_a_run_with_no_analysis_does_not_need_matplotlib(config, hidden, asked):
    hidden.add("matplotlib")
    dependencies.check(options(**asked), config({}))


def test_perfetto_is_needed_only_when_a_device_run_captures_energy(config, hidden, capsys):
    hidden.add("perfetto")
    dependencies.check(options(device=True), config({}))
    captured = config({"harness": {"energy": {"capture": "measured"}}})
    dependencies.check(options(bench=True), captured)
    with pytest.raises(SystemExit):
        dependencies.check(options(device=True), captured)
    assert "missing_dependency: perfetto;" in capsys.readouterr().err


def test_the_manafa_source_needs_manafa_not_perfetto(config, hidden):
    hidden.add("perfetto")
    dependencies.check(options(device=True), config({"harness": {"energy": {"capture": "measured", "source": "manafa"}}}))


def test_the_energy_module_is_looked_for_in_the_energy_python(config):
    captured = config({"harness": {"energy": {"capture": "measured"}}})
    with pytest.raises(SystemExit):
        dependencies.check(options(device=True, energy_python=str(ROOT / "no-such-python")), captured)


def test_the_command_exits_with_the_line_before_a_second_passes(tmp_path):
    # -S hides site-packages, so PyYAML itself is the module missing
    done = subprocess.run([sys.executable, "-S", str(ROOT / "apps/benchmark-runner/dependencies.py"), "--bench"], capture_output=True, text=True,
                          timeout=5, env={"PYTHONPATH": ""}, check=False)
    assert done.returncode == 1
    assert "missing_dependency: yaml" in done.stderr


def test_a_failed_chart_script_is_a_warning_and_analysis_goes_on(tmp_path, monkeypatch, capsys):
    tools = tmp_path / "analysis"
    tools.mkdir(parents=True)
    (tools / "analyze.py").write_text("import no_such_module_at_all\n")
    (tools / "charts.py").write_text("raise SystemExit('never reached')\n")
    monkeypatch.setattr(benchmark, "RUNNER", tmp_path)
    files = {}
    benchmark.analyse(tmp_path, files, tmp_path / "effective.yaml", tmp_path / "preparation", tmp_path / "benchmark", [], 1)
    out = capsys.readouterr().out
    assert out.count("charts_failed") == 1
    assert files["benchmark"] == tmp_path / "benchmark/benchmark.json"
