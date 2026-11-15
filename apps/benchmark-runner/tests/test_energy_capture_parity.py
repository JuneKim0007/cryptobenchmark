"""The runner's copy of the energy capture rule and energy/capture.py, which the --energy-python scripts import, are the same code."""
import ast, pathlib

from cryptobench.shared.settings import energy_capture

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "energy/capture.py"


def functions(path):
    return [ast.dump(node) for node in ast.parse(pathlib.Path(path).read_text()).body if isinstance(node, ast.FunctionDef)]


def test_the_two_copies_define_the_same_functions():
    assert functions(energy_capture.__file__) == functions(SCRIPT) != []
