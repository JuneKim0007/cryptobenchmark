"""apps/benchmark-runner holds the entry points and the scripts run by path; the code a run imports lives in lib/cryptobench."""
import pathlib

RUNNER = pathlib.Path(__file__).resolve().parents[2] / "apps/benchmark-runner"
# failure.py: the entry points' error line, imported before dependencies.py knows cryptobench imports
ENTRY_POINTS = {"pipeline.py", "dependencies.py", "explain.py", "failure.py"}
# energy/ runs under --energy-python, analysis/ as subprocesses by path
BY_PATH = {"energy", "analysis"}


def test_the_runner_holds_only_entry_points_and_scripts_run_by_path():
    found = {p.name for p in RUNNER.iterdir() if p.name not in ("__pycache__", "tests") and not p.name.startswith(".")}
    assert found <= ENTRY_POINTS | BY_PATH, f"move into lib/cryptobench: {sorted(found - ENTRY_POINTS - BY_PATH)}"
