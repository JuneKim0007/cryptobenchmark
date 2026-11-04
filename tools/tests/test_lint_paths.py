import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from lint.paths import is_doc, is_guide


def test_each_router_has_its_own_guides_folder():
    assert is_guide("docs/contributing/code.md") and not is_doc("docs/contributing/code.md")
    assert is_guide("apps/perf-repair/agents/data.md") and not is_guide("apps/perf-repair/docs/contributing/x.md")
    assert is_doc("docs/run.md") and is_doc("apps/perf-repair/docs/settings.md") and not is_guide("agents/code.md")
