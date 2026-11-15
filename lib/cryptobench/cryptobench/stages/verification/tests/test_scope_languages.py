import yaml

from cryptobench.shared import paths
from cryptobench.stages.verification.scope import languages as scope_languages

NAMES = paths.repo().perf_repair_source / "perfrepair/repair/names.yaml"


def test_java_lang_agrees_with_perf_repair_names():
    assert scope_languages.JAVA_LANG == frozenset(yaml.safe_load(NAMES.read_text())["java_lang"])
