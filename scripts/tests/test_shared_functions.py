import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import shared_functions


def test_a_package_and_a_script_of_one_name_are_both_indexed():
    found = shared_functions.modules(["apps/cli"])
    assert found["facade"].as_posix().endswith("apps/cli/facade/__init__.py")
    assert found["facade.py"].as_posix().endswith("apps/cli/facade.py")
    assert ("facade", "SOURCE") in shared_functions.definitions(found)
    assert ("facade.py", "main") in shared_functions.definitions(found)
