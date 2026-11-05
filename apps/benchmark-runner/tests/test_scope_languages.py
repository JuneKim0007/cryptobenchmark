import pathlib, sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scope import languages as scope_languages  # noqa: E402

NAMES = ROOT.parent / "perf-repair/src/perfrepair/repair/names.yaml"


def test_java_lang_agrees_with_perf_repair_names():
    assert scope_languages.JAVA_LANG == frozenset(yaml.safe_load(NAMES.read_text())["java_lang"])
