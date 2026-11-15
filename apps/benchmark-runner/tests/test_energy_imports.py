"""The scripts --energy-python runs import nothing from cryptobench."""
import ast, pathlib

ENERGY = pathlib.Path(__file__).resolve().parents[1] / "energy"


def _imports(path):
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            yield node.module


def test_the_energy_scripts_import_nothing_from_cryptobench():
    scripts = [p for p in ENERGY.rglob("*.py") if "tests" not in p.relative_to(ENERGY).parts]
    assert scripts
    assert [str(p) for p in scripts if any(n.split(".")[0] == "cryptobench" for n in _imports(p))] == []
