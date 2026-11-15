"""energy/ under two import names: one EnergyError for the runner; the scripts --energy-python runs import nothing from cryptobench."""
import ast, pathlib, subprocess, sys

import cryptobench

RUNNER = pathlib.Path(__file__).resolve().parents[1]
ENERGY = RUNNER / "energy"
TWO_NAMES = f"""
import importlib, sys
sys.path[:0] = [{str(RUNNER)!r}, {str(pathlib.Path(cryptobench.__file__).parents[1])!r}]
by_package = importlib.import_module("energy.sources.manafa_source")
import energy_stage
by_folder = importlib.import_module("sources.manafa_source")
from cryptobench.shared.errors.failures import EnergyError
assert by_package is not by_folder
assert by_package.EnergyError is by_folder.EnergyError is EnergyError
"""


def test_the_sources_loaded_under_both_names_raise_one_energy_error():
    result = subprocess.run([sys.executable, "-I", "-c", TWO_NAMES], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def _imports(path):
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            yield node.module


def test_the_energy_scripts_import_nothing_from_cryptobench():
    scripts = [p for p in ENERGY.rglob("*.py") if not {"sources", "tests"} & set(p.relative_to(ENERGY).parts)]
    assert scripts
    assert [str(p) for p in scripts if any(n.split(".")[0] == "cryptobench" for n in _imports(p))] == []
