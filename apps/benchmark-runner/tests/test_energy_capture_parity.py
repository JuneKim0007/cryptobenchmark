"""The runner's copy of the energy capture rule and energy/capture.py, which the --energy-python scripts import, are the same code."""
import ast, pathlib

from cryptobench.shared.settings import energy_capture

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "energy/capture.py"


def statements(path):
    return [ast.dump(node) for node in ast.parse(pathlib.Path(path).read_text()).body[1:]]


def test_the_two_copies_hold_the_same_statements_after_the_docstring():
    assert statements(energy_capture.__file__) == statements(SCRIPT) != []
