"""tools/paths_check.py: each path rule found by the AST, a frozen entry only shrinks, a data file with no reader fails."""
import ast

import paths_check as check


def rules(text):
    return check._rules(ast.parse(text))


def test_each_rule_is_found():
    assert rules("x = __file__") == {"__file__"}
    assert rules("y = a.parents[1]") == {".parents["}
    assert rules("a.with_name('b')") == {"with_name("}
    assert rules("import sys\nsys.path.insert(0, 'a')") == {"sys.path"}
    assert rules("a = 'PYTHONPATH'") == {"PYTHONPATH"}
    assert rules("from pathlib import Path\nPath.home()") == {"Path.home()"}
    assert rules("import os\nos.environ.get('ANDROID_HOME')") == {"env ANDROID_HOME"}
    assert rules("a = 'prepared.yaml'") == {"contract prepared.yaml"}
    assert rules("a = 'apps/benchmark/x'") == {"repo path apps/benchmark/x"}


def test_a_docstring_and_an_error_text_are_not_code():
    assert rules('"""Reads __file__ of apps/x."""\nprint("see apps/x")') == set()
    assert rules('a = f"apps/{b}/benchmark.json"') == set()


def test_a_new_violation_is_a_problem_and_a_fixed_one_must_leave(tmp_path):
    frozen = tmp_path / "frozen.txt"
    frozen.write_text("a: rule # why\nb: rule\n")
    assert check.check({"a: rule", "c: rule"}, frozen, shrink=False) == ["new: c: rule", "fixed, remove from frozen.txt (--shrink): b: rule"]
    assert check.check({"a: rule"}, frozen, shrink=True) == []
    assert frozen.read_text() == "a: rule # why\n"


def test_a_data_file_without_a_reader_is_flagged(tmp_path):
    assert check._read_in({"families.yaml"}, tmp_path / "families.yaml")
    assert not check._read_in({"other.yaml"}, tmp_path / "families.yaml")
