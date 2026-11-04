"""tools/unrun.py: the functions a recorded run never entered."""
import importlib.util
import sys
from pathlib import Path

import pytest

coverage = pytest.importorskip("coverage")
TOOL = Path(__file__).parents[1] / "tools" / "unrun.py"
SOURCE = '''def called():
    return 1


def never():
    return 2


class Box:
    def opened(self):
        return 3

    def shut(self):
        return 4
'''


def test_only_the_functions_no_run_entered_are_listed(tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "sample.py").write_text(SOURCE)
    data = tmp_path / ".coverage"
    cov = coverage.Coverage(data_file=str(data), source=[str(source)])
    sys.path.insert(0, str(source))
    try:
        cov.start()
        import sample
        sample.called()
        sample.Box().opened()
        cov.stop()
        cov.save()
    finally:
        sys.path.remove(str(source))
        sys.modules.pop("sample", None)
    spec = importlib.util.spec_from_file_location("unrun", TOOL)
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    assert tool.unrun(data, source) == ["sample.py:5 never", "sample.py:13 Box.shut"]
