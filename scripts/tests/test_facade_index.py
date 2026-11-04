import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from facade.index import SettingsIndexError, read_index
from repo import ROOT

GOOD = "schemaVersion: 1\nresults: r\ncrypto: {config: c/global.yaml}\nllm: {config: l/p.yaml}\n"


def index(tmp_path, text):
    (tmp_path / "s.yaml").write_text(text)
    return read_index(tmp_path / "s.yaml")


def test_paths_resolve_against_the_file_holding_them(tmp_path):
    found = index(tmp_path, GOOD + "run: {id: one, onExisting: resume}\n")
    assert (found.results, found.crypto_config, found.llm_config) == (tmp_path / "r", tmp_path / "c/global.yaml", tmp_path / "l/p.yaml")
    assert (found.run_id, found.on_existing, found.harness_config) == ("one", "resume", None)


def test_an_empty_run_takes_a_new_id_and_overwrites(tmp_path):
    found = index(tmp_path, GOOD + "run: {id: , onExisting: }\n")
    assert (found.run_id, found.on_existing) == (None, "overwrite")


@pytest.mark.parametrize("extra, code", [
    ("typo: 1\n", "unknown_key: ['typo']"),
    ("crypto2: {}\n", "unknown_key: ['crypto2']"),
    ("run: {seed: 1}\n", "unknown_key: run.['seed']"),
    ("run: {onExisting: never}\n", "invalid: run.onExisting never"),
    ("run: {id: 'a/b'}\n", "invalid: run.id a/b"),
    ("run: 3\n", "invalid: run in"),
])
def test_a_bad_key_is_one_coded_line(tmp_path, extra, code):
    with pytest.raises(SettingsIndexError, match="^" + code.replace("[", r"\[").replace("]", r"\]")):
        index(tmp_path, GOOD + extra)


@pytest.mark.parametrize("text, code", [
    ("schemaVersion: 2\nresults: r\ncrypto: {config: c}\nllm: {config: l}\n", "wrong_version"),
    ("schemaVersion: 1\ncrypto: {config: c}\nllm: {config: l}\n", "missing_key: results"),
    ("schemaVersion: 1\nresults: r\nllm: {config: l}\n", "missing_key: crypto.config"),
    ("schemaVersion: 1\nresults: r\ncrypto: {config: c}\n", "missing_key: llm.config"),
    ("[1]\n", "invalid:"),
    ("a: [\n", "invalid_yaml"),
])
def test_a_bad_file_is_one_coded_line(tmp_path, text, code):
    with pytest.raises(SettingsIndexError, match="^" + code):
        index(tmp_path, text)


def test_no_file_is_missing_file(tmp_path):
    with pytest.raises(SettingsIndexError, match="^missing_file"):
        read_index(tmp_path / "none.yaml")


def test_the_example_is_a_good_index():
    found = read_index(ROOT / "settings.example.yaml")
    assert found.crypto_config == ROOT / "config/global.yaml" and found.llm_config == ROOT / "perf-repair/perfrepair.yaml"
