import pathlib

from cryptobench.shared import paths
from cryptobench.shared.digest.tree import globbed
from cryptobench.shared.results import partial


def test_desktop_litter_is_named_and_a_run_file_is_not():
    assert all(paths.litter(pathlib.Path(name)) for name in (".DS_Store", "._benchmark.json", "Thumbs.db", "desktop.ini"))
    assert not any(paths.litter(pathlib.Path(name)) for name in ("benchmark.json", ".lock", "block-1.yaml"))


def test_a_source_digest_and_a_partial_count_skip_litter(tmp_path):
    cases = paths.Measurement(tmp_path / "benchmark").cases
    cases.mkdir(parents=True)
    for name in ("a.json", "._a.json", ".DS_Store"):
        (cases / name).write_text("{}")
    assert globbed(tmp_path, ["benchmark/**/*"]) == ([cases / "a.json"], [])
    assert partial.done(tmp_path / "benchmark") == {"caseRuns": 1, "cases": 1, "processes": {".": 1}}
